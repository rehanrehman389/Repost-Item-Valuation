class StockLedgerEntry:

    def __init__(self):
        self.entries = []

    def add(self, item, warehouse, quantity, valuation_rate, voucher=None, depends_on_item=None):
        previous_quantity = 0
        previous_fifo_queue = []

        for entry in reversed(self.entries):
            if (
                entry["item"] == item
                and entry["warehouse"] == warehouse
            ):
                previous_quantity = entry["quantity_after"]

                previous_fifo_queue = [fifo_layer.copy() for fifo_layer in entry["fifo_queue"]]
                break

        quantity_after = previous_quantity + quantity

        fifo_queue = previous_fifo_queue

        # Stock IN

        if quantity > 0:
            fifo_queue.append([quantity, valuation_rate])
            cost = quantity * valuation_rate

        # Stock OUT

        else:
            quantity_to_consume = abs(quantity)

            total_consumption_cost = 0

            while quantity_to_consume > 0:
                fifo_layer = fifo_queue[0]

                available_quantity = fifo_layer[0]

                consumed_quantity = min(quantity_to_consume, available_quantity)
                
                total_consumption_cost += (consumed_quantity * fifo_layer[1])

                fifo_layer[0] -= consumed_quantity
                quantity_to_consume -= consumed_quantity

                if fifo_layer[0] == 0:
                    fifo_queue.pop(0)

                cost = total_consumption_cost

        self.entries.append(
            {
                "item": item,
                "warehouse": warehouse,
                "quantity": quantity,
                "valuation_rate": valuation_rate,
                "quantity_after": quantity_after,
                "fifo_queue": fifo_queue,
                "voucher": voucher,
                "depends_on_item": depends_on_item,
                "cost": cost,
            }
        )

    def manufacture(
        self,
        voucher,
        raw_material_item,
        raw_material_quantity,
        finished_item,
        finished_quantity,
        warehouse,
    ):
        # RM
        self.add(
            item=raw_material_item,
            warehouse=warehouse,
            quantity=-raw_material_quantity,
            valuation_rate=60,
            voucher=voucher,
        )

        # FG
        self.add(
            item=finished_item,
            warehouse=warehouse,
            quantity=finished_quantity,
            valuation_rate=0,
            voucher=voucher,
            depends_on_item=raw_material_item,
        )

    def change_rate(self, index, new_valuation_rate):
        self.entries[index]["valuation_rate"] = new_valuation_rate

    def repost(self):

        total_consumption_cost = 0
        balances = {}
        fifo_queues = {}

        manufacturing_cost_by_voucher = {}

        for entry in self.entries:
            stock_key = (
                entry["item"],
                entry["warehouse"],
            )

            if stock_key not in balances:
                balances[stock_key] = 0

            if stock_key not in fifo_queues:
                fifo_queues[stock_key] = []

            # Stock IN

            if entry["quantity"] > 0:
                valuation_rate = entry["valuation_rate"]

                if entry["depends_on_item"]:
                    manufacturing_cost = (
                        manufacturing_cost_by_voucher.get(
                            entry["voucher"],
                            0,
                        )
                    )

                    valuation_rate = (
                        manufacturing_cost
                        / entry["quantity"]
                    )

                    entry["valuation_rate"] = valuation_rate

                balances[stock_key] += entry["quantity"]

                fifo_queues[stock_key].append([entry["quantity"], valuation_rate])

                entry["cost"] = entry["quantity"] * valuation_rate

            # Stock OUT

            else:
                quantity_to_consume = abs(entry["quantity"])

                total_consumption_cost = 0

                while quantity_to_consume > 0:
                    fifo_layer = fifo_queues[stock_key][0]

                    available_quantity = fifo_layer[0]

                    consumed_quantity = min(quantity_to_consume, available_quantity)

                    total_consumption_cost += (consumed_quantity * fifo_layer[1])

                    fifo_layer[0] -= consumed_quantity
                    quantity_to_consume -= consumed_quantity

                    if fifo_layer[0] == 0:
                        fifo_queues[stock_key].pop(0)

                balances[stock_key] -= abs(
                    entry["quantity"]
                )

                entry["valuation_rate"] = (
                    total_consumption_cost
                    / abs(entry["quantity"])
                )

                entry["cost"] = total_consumption_cost

                if entry["voucher"]:
                    manufacturing_cost_by_voucher[
                        entry["voucher"]
                    ] = (
                        manufacturing_cost_by_voucher.get(
                            entry["voucher"],
                            0,
                        )
                        + total_consumption_cost
                    )


            entry["quantity_after"] = balances[stock_key]

            entry["fifo_queue"] = [
                fifo_layer.copy()
                for fifo_layer in fifo_queues[stock_key]
            ]

    def show(self):
        for entry in self.entries:
            print(
                entry["voucher"],
                entry["item"],
                entry["warehouse"],
                entry["quantity"],
                entry["valuation_rate"],
                entry["cost"],
                entry["fifo_queue"],
                entry["depends_on_item"],
                entry["quantity_after"],
            )


ledger = StockLedgerEntry()

print("\nBEFORE CHANGE")
ledger.add("Milk", "Warehouse A", 100, 50, voucher="PR-001")
ledger.add("Milk", "Warehouse A", 50, 60, voucher="PR-002")
ledger.add("Milk", "Warehouse A", -80, 50, voucher="DN-001")
ledger.add("Milk", "Warehouse A", 50, 60, voucher="PR-003")
ledger.manufacture(voucher="ME-001", raw_material_item="Milk", raw_material_quantity=100, finished_item="Milk Powder", finished_quantity=10, warehouse="Warehouse A")
ledger.add("Milk Powder", "Warehouse A", -10, None, voucher="DN-001",)
ledger.show()

print("\nAFTER RATE CHANGE - BEFORE REPOST")
ledger.change_rate(index=1, new_valuation_rate=80)
ledger.show()

print("\nAFTER REPOST")
ledger.repost()
ledger.show()
