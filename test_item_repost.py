import unittest
from item_repost import StockLedgerEntry

class TestStockLedger(unittest.TestCase):

    def test_repost_after_second_layer_rate_change(self):
        ledger = StockLedgerEntry()
    
        ledger.add("Milk", "Warehouse A", 100, 50)
        ledger.add("Milk", "Warehouse A", 50, 60)
        ledger.add("Milk", "Warehouse A", -120, None)
    
        ledger.change_rate(index=1, new_valuation_rate=80)
        ledger.repost()
    
        entry = ledger.entries[2]
        self.assertEqual(entry["valuation_rate"], 55)
        self.assertEqual(entry["quantity_after"], 30)
        self.assertEqual(entry["fifo_queue"], [[30, 80]])
  
  
    def test_repost_after_first_layer_rate_change(self):
        ledger = StockLedgerEntry()
    
        ledger.add("Milk", "Warehouse A", 100, 50)
        ledger.add("Milk", "Warehouse A", 50, 60)
        ledger.add("Milk", "Warehouse A", -80, None)
    
        ledger.change_rate(index=0, new_valuation_rate=80)
        ledger.repost()
    
        entry = ledger.entries[2]
        self.assertEqual(entry["valuation_rate"], 80)
        self.assertEqual(entry["quantity_after"], 70)
        self.assertEqual(entry["fifo_queue"], [[20, 80], [50, 60]])
  
  
    def test_repost_after_rate_change_updates_dependent_cost(self):
        ledger = StockLedgerEntry()
    
        ledger.add("Milk", "Warehouse A", 100, 50)
        ledger.add("Milk", "Warehouse A", 100, 60)
        ledger.manufacture(
            voucher="ME-001",
            raw_material_item="Milk",
            raw_material_quantity=100,
            finished_item="Milk Powder",
            finished_quantity=10,
            warehouse="Warehouse A",
        )
        
        ledger.change_rate(index=0, new_valuation_rate=80)
        ledger.repost()
    
        raw_material = ledger.entries[2]
        finished_good = ledger.entries[3]
        self.assertEqual(raw_material["valuation_rate"], 80)
        self.assertEqual(finished_good["valuation_rate"], 800)
  
  
    def test_repost_keeps_warehouse_fifo_separate(self):
        ledger = StockLedgerEntry()
    
        # Warehouse A
        ledger.add("Milk", "Warehouse A", 100, 50)
        ledger.add("Milk", "Warehouse A", -80, None)
    
        # Warehouse B
        ledger.add("Milk", "Warehouse B", 100, 100)
        ledger.add("Milk", "Warehouse B", -80, None)
    
        ledger.change_rate(index=0, new_valuation_rate=80)
        ledger.repost()
    
        warehouse_a_consumption = ledger.entries[1]
        warehouse_b_consumption = ledger.entries[3]
    
        self.assertEqual(warehouse_a_consumption["valuation_rate"], 80)
        self.assertEqual(warehouse_b_consumption["valuation_rate"], 100)
  
  
    def test_repost(self):
        ledger = StockLedgerEntry()
    
        ledger.add("Milk", "Warehouse A", 100, 50)
        ledger.add("Milk", "Warehouse A", 50, 60)
        ledger.add("Milk", "Warehouse A", -80, None)
        ledger.add("Milk", "Warehouse A", 50, 60)
        ledger.manufacture(
            voucher="ME-001",
            raw_material_item="Milk",
            raw_material_quantity=100,
            finished_item="Milk Powder",
            finished_quantity=10,
            warehouse="Warehouse A",
        )
        ledger.add("Milk Powder", "Warehouse A", -10, None, voucher="DN-001")
    
        ledger.change_rate(index=1, new_valuation_rate=80)
        ledger.repost()
    
        self.assertEqual(ledger.entries[2]["valuation_rate"], 50)
        
        raw_material = ledger.entries[4]
        self.assertEqual(raw_material["valuation_rate"], 68)
        self.assertEqual(raw_material["cost"], 6800)
    
        finished_good = ledger.entries[5]
        self.assertEqual(finished_good["valuation_rate"], 680)
        self.assertEqual(finished_good["cost"], 6800)
    
        finished_good_consumption = ledger.entries[6]
        self.assertEqual(finished_good_consumption["valuation_rate"], 680)
        self.assertEqual(finished_good_consumption["cost"], 6800)
        self.assertEqual(finished_good_consumption["quantity_after"], 0)


if __name__ == "__main__":
    unittest.main()
