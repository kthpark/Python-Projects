import os
import sqlite3

from hstest import CheckResult, StageTest, dynamic_test, TestedProgram

db_name = "investor.db"
table_names = ["companies", "financial"]
files_to_delete = ("investor.db",)

main_menu = """
MAIN MENU
0 Exit
1 CRUD operations
2 Show top ten companies by criteria
"""

top_ten_menu = """
TOP TEN MENU
0 Back
1 List by ND/EBITDA
2 List by ROE
3 List by ROA
"""

ebitda_msg = """TICKER ND/EBITDA
DUK 6.4
SO 6.02
CHTR 4.55
NEE 4.39
TMUS 4.19
DE 4.16
T 3.94
MCD 3.77
VZ 3.57
CAT 3.34"""

roe_msg = """TICKER ROE
AMGN 6.43
AAPL 1.4
MA 1.22
UPS 0.84
ABBV 0.7
QCOM 0.68
LMT 0.63
ADP 0.62
LLY 0.59
TXN 0.55"""

roa_msg = """TICKER ROA
TXN 0.31
AAPL 0.27
FB 0.24
MA 0.23
HD 0.23
AMAT 0.23
NVDA 0.22
PM 0.22
GOOG 0.21
QCOM 0.2"""

welcome_msg = "Welcome to the Investor Program!"
farewell_msg = "Have a nice day!"
ask_option_msg = "Enter an option:"
invalid_option_msg = "Invalid option!"

# index 0 entered value, index 1 expected value
test_data_1 = [
    {
        "test_values": [
            ("2", (top_ten_menu + ask_option_msg)),
            ("199", (invalid_option_msg + main_menu + ask_option_msg)),
            ("2", (top_ten_menu + ask_option_msg)),
            ("1", (ebitda_msg + main_menu + ask_option_msg)),
            ("0", farewell_msg),
        ]
    },
    {
        "test_values": [
            ("2", (top_ten_menu + ask_option_msg)),
            ("2", (roe_msg + main_menu + ask_option_msg)),
            ("0", farewell_msg),
        ]
    },
    {
        "test_values": [
            ("2", (top_ten_menu + ask_option_msg)),
            ("3", (roa_msg + main_menu + ask_option_msg)),
            ("0", farewell_msg),
        ]
    },
]


def delete_files(arr):
    for file_name in arr:
        if os.path.exists(file_name):
            os.remove(file_name)


class InvestorTest(StageTest):
    def after_all_tests(self):
        delete_files(files_to_delete)

    # testing entered vs expected
    @dynamic_test(data=test_data_1)
    def test1(self, dict_):
        t = TestedProgram()
        output = t.start().strip()
        text = welcome_msg.strip() + main_menu.strip() + ask_option_msg.strip()
        if output.replace("\n", "") != text.replace("\n", ""):
            # print(repr(output))
            # print(repr(text))
            return CheckResult.wrong(
                f"Your program should output:\n{text}\ninstead of:\n{output}")
        for test_values in dict_.values():
            for item in test_values:
                output = t.execute(item[0]).strip()
                text = item[1]
                if output.replace("\n", "") != text.replace("\n", ""):
                    # print(repr(output))
                    # print(repr(text))
                    return CheckResult.wrong(
                        f"Your program should output:\n{text}\ninstead of:\n{output}")
        return CheckResult.correct()

    # testing if database exists
    @dynamic_test()
    def test2(self):
        if not os.path.exists(db_name):
            return CheckResult.wrong(
                f"'{db_name}' does not exist!")
        return CheckResult.correct()

    # testing if tables exist
    @dynamic_test()
    def test3(self):
        conn = sqlite3.connect(db_name)
        cur = conn.cursor()
        for table in table_names:
            query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';"
            cur.execute(query)
            r = cur.fetchall()
            if not r or r[0][0] != table:
                conn.close()
                return CheckResult.wrong(f"Table {table} not found!")
        conn.close()
        return CheckResult.correct()


if __name__ == '__main__':
    InvestorTest().run_tests()
