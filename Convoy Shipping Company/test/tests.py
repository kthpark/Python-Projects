from hstest.stage_test import *
from hstest.test_case import TestCase
from os import path
import shutil
import re
import sqlite3
import json
import os
import hashlib
import requests
import zipfile


class EasyRiderStage1(StageTest):
    files_to_delete = []
    files_to_check = ["data_one_xlsx.xlsx", "data_big_xlsx.xlsx", "data_one_csv.csv", "data_big_csv.csv",
                      "data_one_chk[CHECKED].csv", "data_big_chk[CHECKED].csv", "data_big_sql.s3db", "data_final_xlsx.xlsx"]

    def s3db_generate(self, name):
        name = os.path.join("test", name.strip("chk[CHECKED].csv"))
        self.files_to_delete.append(f'{name}sql.s3db')
        with open(f'{name.strip()}chk[CHECKED].csv', 'r', encoding='utf-8') as file:
            db_convoy = file.readline().strip().split(",")
            conn = sqlite3.connect(f'{name}sql.s3db')
            convoy = conn.cursor()
            convoy.execute(f"CREATE TABLE convoy({db_convoy[0]} "
                           f"INTEGER PRiMARY KEY, {db_convoy[1]} "
                           f"INTEGER NOT NULL, {db_convoy[2]} "
                           f"INTEGER NOT NULL, {db_convoy[3]} "
                           f"INTEGER NOT NULL, "
                           f"score INTEGER NOT NULL);")
            conn.commit()
            for line in file:
                line = line.strip().split(",")
                distance = 450 / 100
                score1 = (distance * int(line[2])) / int(line[1])
                s1 = 0 if score1 > 2 else 1 if score1 >= 1 else 2
                s2 = 2 if distance * int(line[2]) <= 230 else 1
                s3 = 2 if int(line[3]) >= 20 else 0
                score = s1 + s2 + s3
                convoy.execute(f"INSERT INTO convoy({db_convoy[0]},{db_convoy[1]},{db_convoy[2]},{db_convoy[3]},score) VALUES({line[0]},{line[1]},{line[2]},{line[3]},{score})")
            conn.commit()
            conn.close()

    def remove_s3db_files(self):
        for name in [names.split(".")[0].strip("[CHECKED]") + ".s3db" for names in self.files_to_check]:
            name_del = os.path.join("test", name)
            if path.exists(name_del):
                try:
                    os.remove(name_del)
                except PermissionError:
                    raise WrongAnswer(f"Can't delete the database file: {name_del}. Looks like database connection wasn't closed or database is open in external program.")

    def generate(self) -> List[TestCase]:
        check_test_files("https://stepik.org/media/attachments/lesson/461165/stage6_files.zip")
        self.remove_s3db_files()
        self.s3db_generate("data_big_chk[CHECKED].csv")
        return [
                TestCase(stdin=[self.prepare_file], attach=("data_one_xlsx.xlsx", 1, "line", 4, "cell", 488, "record", "vehicle", 494, 1, 0)),
                TestCase(stdin=[self.prepare_file], attach=("data_big_xlsx.xlsx", 10, "line", 12, "cell", 5961, "record", "vehicle", 6003, 7, 3)),
                TestCase(stdin=[self.prepare_file], attach=("data_one_csv.csv", 1, None, 4, "cell", 488, "record", "vehicle", 494, 1, 0)),
                TestCase(stdin=[self.prepare_file], attach=("data_big_csv.csv", 10, None, 12, "cell", 5961, "record", "vehicle", 6003, 7, 3)),
                TestCase(stdin=[self.prepare_file], attach=("data_one_chk[CHECKED].csv", 1, None, None, "cell", 488, "record", "vehicle", 494, 1, 0)),
                TestCase(stdin=[self.prepare_file], attach=("data_big_chk[CHECKED].csv", 10, None, None, "cell", 5961, "record", "vehicle", 6003, 7, 3)),
                TestCase(stdin=[self.prepare_file], attach=("data_big_sql.s3db", 10, None, None, "cell", 5961, "record", "vehicle", 6811, 7, 3)),
                TestCase(stdin=[self.prepare_file], attach=("data_final_xlsx.xlsx", 19, "line", 3, "cell", 8121, "record", "vehicle", 8194, 12, 7)),
        ]

    def after_all_tests(self):
        for file in set(self.files_to_delete):
            try:
                os.remove(file)
            except PermissionError:
                raise WrongAnswer(f"Can't delete the database file: {file}. Looks like database connection wasn't closed.")

    def prepare_file(self, output):
        file_name = self.files_to_check.pop(0)
        shutil.copy(os.path.join("test", file_name), os.path.join("."))
        self.files_to_delete.append(file_name)
        return file_name

    def file_exist(self, file_name):
        if not path.exists(file_name):
            return f"The file '{file_name}' does not exist or is outside of the script directory."
        self.files_to_delete.append(file_name)
        return False

    @staticmethod
    def wrong_number_of_lines_csv(file_name, nr):
        with open(file_name, 'r', encoding='utf-8') as file_csv:
            csv_len = len([x for x in file_csv]) - 1
            if csv_len != nr:
                return f"Wrong number of lines in file {file_name}. Expected {nr}, found {csv_len}\n" + \
                       "check if you have imported headers and all data is present;\ncheck if you have imported the appropriate sheet.)"
        return False

    @staticmethod
    def check_output(quantity, nr, text, file_name):
        prefix = f"{quantity} {nr}{' was' if quantity == 1 else 's were'}"
        if not text.startswith(prefix):
            return f"Output don't starts with sentence '{prefix}' in output '{text}'"
        if file_name not in text:
            return f"There is no {file_name} name in output '{text}'."
        return False

    @staticmethod
    def quality_of_data_csv(file_name, number):
        count = 0
        try:
            with open(file_name, 'r', encoding='utf-8') as file:
                for line in file:
                    if not line.startswith("vehicle_id"):
                        for item in line.split(","):
                            if not re.match(r"^[\d]+$", item):
                                return f"In line '{line.strip()}': '{item}' is not a number. Check {file_name}"
                            count += int(item)
        except UnicodeDecodeError:
            return f"The CSV file is not UTF-8 encoded."
        if count != number:
            return f"Check data in {file_name}. Sum of integer should be {number}, found {count}"
        return False

    @staticmethod
    def checking_database(file_name, nr_lines, number):
        conn = sqlite3.connect(file_name)
        convoy = conn.cursor()

        #  checking if table exists
        try:
            lines = convoy.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='convoy';").fetchall()
        except sqlite3.DatabaseError as er:
            return f"Attempting to read from the {file_name} database generates the error: {er}."
        if lines[0][0] == 0:
            return f"There is no table named 'convoy' in database {file_name}"

        #  counting number of the records
        lines = convoy.execute("SELECT COUNT(*) FROM convoy").fetchone()[0]
        if lines != nr_lines:
            return f"Wrong number of records in database {file_name}. Expected {nr_lines}, found {lines}"

        #  checking column names
        lines = convoy.execute('select * from convoy').description
        if sorted([x[0] for x in lines]) != sorted(['vehicle_id', 'engine_capacity', 'fuel_consumption', 'maximum_load', 'score']):
            return f"There is something wrong in {file_name}. Found column names: {[x[0] for x in lines]}. " + \
                   "Expected five columns names: 'vehicle_id', 'engine_capacity', 'fuel_consumption', 'maximum_load', 'score'"

        #  checking sum of cells
        all_lines = convoy.execute("SELECT * FROM convoy")
        try:
            count = sum(sum(x) for x in all_lines.fetchall())
        except TypeError:
            return f"There is a value other than INTEGER in the table."
        if count != number:
            return f"Check data. Sum of integer in '.s3db' should be {number}, found {count}."

        #  checking if PRIMARY KEY exists
        all_lines = convoy.execute("SELECT * FROM convoy")
        p_key = all_lines.fetchall()[0][0]
        try:
            convoy.execute(f"INSERT INTO convoy(vehicle_id,engine_capacity,fuel_consumption,maximum_load,score) VALUES({p_key},0,0,0,0)")
        except sqlite3.IntegrityError:
            pass
        else:
            return f"There is no PRIMARY KEY parameter on column 'vehicle_id' in {file_name}."

        #  checking if columns have an attribute NOT NULL
        not_null = (('1000', 'Null', '1', '1', '1'), ('1001', '1', 'Null', '1', '1'), ('1002', '1', '1', 'Null', '1'), ('1003', '1', '1', '1', 'Null'))
        for values in not_null:
            try:
                convoy.execute(f"INSERT INTO convoy(vehicle_id,engine_capacity,fuel_consumption,maximum_load, score) "
                               f"VALUES({values[0]},{values[1]},{values[2]},{values[3]},{values[4]})")
            except sqlite3.IntegrityError:
                pass
            else:
                return f"At least one of the columns has no 'NOT NULL' parameter in {file_name}."

        conn.close()
        return False

    @staticmethod
    def checking_json(file_name, number):
        fields = ['vehicle_id', 'engine_capacity', 'fuel_consumption', 'maximum_load']
        count = 0
        with open(file_name, "r") as json_file:
            try:
                from_json = json.load(json_file)
            except json.decoder.JSONDecodeError:
                return f"There is different data type in JSON file than JSON."

        # checking is there a score key
        try:
            if from_json["convoy"][0]["score"]:
                return f"There is 'score' key in JSON file"
        except KeyError:
            pass
        except IndexError:
            return f"There are no items in the JSON dictionary."
        except TypeError:
            return f"There is different data type in JSON file than dictionary."

        #  check is there expected number of items and are there all keys
        if len(from_json["convoy"]) != number:
            return rf"Wrong number of items in JSON file. Expected {number}, found {len(from_json['convoy'])}."
        try:
            for item in from_json["convoy"]:
                for field in fields:
                    try:
                        count += int(item[field])
                    except KeyError:
                        return f"There is no '{field}' key in record {item} in JSON file."
        except KeyError:
            return f"There is no 'convoy' key in {file_name}."
        except TypeError:
            return f"There is different data type in JSON file than dictionary."
        return False

    @staticmethod
    def checking_xml(file_name, lines):
        tags = {'vehicle_id': lines, 'engine_capacity': lines, 'fuel_consumption': lines, 'maximum_load': lines}
        tags_no_data = {'convoy': 1, 'vehicle': lines}
        with open(file_name, "r") as xml_file:
            from_xml = xml_file.readlines()
        from_xml = "".join(x.strip("\n") for x in from_xml)

        #  checking is there a score key
        if re.findall(rf"<score>", from_xml):
            return f"There is 'score' tag in XML file"

        #  checking number of tags with digits between
        for tag in tags:
            f_tag, l_tag = rf"<{tag}>", rf"</{tag}>"
            n_tags = len(re.findall(rf"({f_tag})[\d]+({l_tag})", from_xml))
            if n_tags != tags[tag]:
                return rf"There is wrong number of {f_tag} tags in {file_name}. Expected {tags[tag]}," + \
                       f" found {n_tags} or there is something more then digits between those tags."

        #  checking high-level tag, and tags without digits between
        for tag in tags_no_data:
            for one_tag in (rf"<{tag}>", rf"</{tag}>"):
                len_t = len(re.findall(rf"({one_tag})", from_xml))
                if len_t != tags_no_data[tag]:
                    return rf"Wrong number of {one_tag} tags in {file_name}. Expected {tags_no_data[tag]}, found {len_t}."

        #  checking structure of file
        template = r"^[\s]*(<convoy>)"
        for x in range(lines):
            template += r"[\s]*(<vehicle>)"
            for key in tags:
                template += fr"[\s]*(<{key}>)[\d]+(</{key}>)"
            template += r"[\s]*(</vehicle>)"
        template += r"[\s]*(</convoy>)[\s]*$"
        if not re.match(template, from_xml):
            return f"There is wrong structure of xml file. Look at the example in the stage description."

        return False

    def check(self, reply: str, result) -> CheckResult:
        if "input" not in reply.lower():
            return CheckResult.wrong(f"The first line of the output should be 'Input file name'")
        reply = reply.splitlines()
        reply.pop(0)
        if len(reply) == 0:
            return CheckResult.wrong(f"There is not enough lines in the output")
        file_name = result[0].split(".")

        #  => xlsx
        if file_name[1] == "xlsx":

            test = self.file_exist(f'{file_name[0]}.csv')
            if test:
                return CheckResult.wrong(test)

            test = self.wrong_number_of_lines_csv(f'{file_name[0]}.csv', result[1])
            if test:
                return CheckResult.wrong(test)

            test = self.check_output(result[1], result[2], reply[0], f'{file_name[0]}.csv')
            if test:
                return CheckResult.wrong(test)

            reply.pop(0)
            if len(reply) == 0:
                return CheckResult.wrong(f"There is not enough lines in the output")

        #  => csv
        if any([file_name[1] == "xlsx", all([file_name[1] == "csv", not ".".join(file_name).endswith("[CHECKED].csv")])]):

            test = self.file_exist(f'{file_name[0]}[CHECKED].csv')
            if test:
                return CheckResult.wrong(test)

            test = self.quality_of_data_csv(f'{file_name[0]}[CHECKED].csv', result[5])
            if test:
                return CheckResult.wrong(test)

            test = self.check_output(result[3], result[4], reply[0], f'{file_name[0]}[CHECKED].csv')
            if test:
                return CheckResult.wrong(test)

            reply.pop(0)
            if len(reply) == 0:
                return CheckResult.wrong(f"There is not enough lines in the output")

        #  => [CHECKED]csv
        if any([file_name[1] == "xlsx", file_name[1] == "csv", ".".join(file_name).endswith("[CHECKED].csv")]):

            file_name[0] = file_name[0].strip("[CHECKED]")
            test = self.file_exist(f'{file_name[0]}.s3db')
            if test:
                return CheckResult.wrong(test)

            test = self.checking_database(f'{file_name[0]}.s3db', result[1], result[8])
            if test:
                return CheckResult.wrong(test)

            test = self.check_output(result[1], result[6], reply[0], f'{file_name[0]}.s3db')
            if test:
                return CheckResult.wrong(test)

            reply.pop(0)
            if len(reply) == 0:
                return CheckResult.wrong(f"There is not enough lines in the output")

        #  => s3db
        test = self.file_exist(f'{file_name[0]}.json')
        if test:
            return CheckResult.wrong(test)

        test = self.checking_json(f'{file_name[0]}.json', result[9])
        if test:
            return CheckResult.wrong(test)

        test = self.check_output(result[9], result[7], reply[0], f'{file_name[0]}.json')
        if test:
            return CheckResult.wrong(test)

        reply.pop(0)
        if len(reply) == 0:
            return CheckResult.wrong(f"There is not enough lines in the output")

        test = self.file_exist(f'{file_name[0]}.xml')
        if test:
            return CheckResult.wrong(test)

        test = self.checking_xml(f'{file_name[0]}.xml', result[10])
        if test:
            return CheckResult.wrong(test)

        test = self.check_output(result[10], result[7], reply[0], f'{file_name[0]}.xml')
        if test:
            return CheckResult.wrong(test)

        return CheckResult.correct()


def extract_files(file_url):
    r = requests.get(file_url, allow_redirects=True)  # download file to local repository
    with open("tmp_test.zip", 'wb') as tmp_file:
        tmp_file.write(r.content)

    with zipfile.ZipFile("tmp_test.zip", 'r') as zip_object:  # unpack zip
        list_of_files = zip_object.namelist()
        for org_file in list_of_files:
            zip_object.extract(org_file)

    if path.exists("tmp_test.zip"):  # delete local zip file
        os.remove("tmp_test.zip")


def check_test_files(file_url):  # as input http address of the zip file on Stpeik
    direct = "test"
    md5_sum = {'data_big_chk[CHECKED].csv': '5f87334c2c4f22e5bfb8a6641fea4f1d',
               'data_big_csv.csv': 'ce035f34f6591e089c3bfc4d0cddab03',
               'data_big_xlsx.xlsx': '12ad1512574f861725dbc82286237697',
               'data_final_xlsx.xlsx': '7166ec4884dc5758067e6da1f4ef884a',
               'data_one_chk[CHECKED].csv': 'cdf1d3fae0ccd85fbfac9aa041c0d455',
               'data_one_csv.csv': '8e3828c13e2c3dd380d6fa2eb22337a1',
               'data_one_xlsx.xlsx': '6b8c741538067a24e7c6bfa39c8b3d94'}

    for file in md5_sum:
        try:
            with open(os.path.join(direct, file), "rb") as local_file:
                content = local_file.read()  # reed content and calculate hash value
                md5_hash = hashlib.md5()
                md5_hash.update(content)
                digest = md5_hash.hexdigest()

                if md5_sum[file] != digest:  # if wrong hash value restore all files
                    extract_files(file_url)
                    return

        except FileNotFoundError:  # if there is no file restore all files
            extract_files(file_url)
            return


if __name__ == '__main__':
    EasyRiderStage1().run_tests()
