import sqlite3
from sqlite3 import Error
import menus


def top10_menu():
    print(menus.TOP_TEN_MENU)
    cmd = input('Enter an option:\n')
    match cmd:
        case '0':
            pass
        case '1':
            list_top10('ND/EBITDA')
        case '2':
            list_top10('ROE')
        case '3':
            list_top10('ROA')
        case _:
            print('Invalid option!\n')


def crud_menu():
    while True:
        print(menus.CRUD_MENU)
        cmd = input('Enter an option:\n')
        match cmd:
            case '0':
                pass
            case '1':
                new_company()
            case '2':
                read_comp()
            case '3':
                upd_comp()
            case '4':
                del_comp()
            case '5':
                list_all()
            case _:
                print('Invalid option!\n')


def main_menu():
    while True:
        print(menus.MAIN_MENU)
        cmd = input('Enter an option:\n')
        match cmd:
            case'0':
                print('Have a nice day!')
                quit()
            case '1':
                crud_menu()
            case '2':
                top10_menu()
            case _:
                print('Invalid option!\n')


def create_tables(conn):
    sql1 = """CREATE TABLE IF NOT EXISTS companies (
                ticker TEXT PRIMARY KEY,
                name TEXT,
                sector TEXT
            ); """
    sql2 = """CREATE TABLE IF NOT EXISTS financial (
                ticker TEXT PRIMARY KEY,
                ebitda REAL,
                sales REAL,
                net_profit REAL,
                market_price REAL,
                net_debt REAL,
                assets REAL,
                equity REAL,
                cash_equivalents REAL,
                liabilities REAL DEFAULT None
            ); """
    try:
        c = conn.cursor()
        c.execute(sql1)
        c.execute(sql2)
        sql = 'SELECT COUNT(ticker) FROM companies'
        cnt = c.execute(sql).fetchone()
        return cnt[0]
    except Error as e:
        print(e)


def new_company():
    vals = []
    for s in menus.COMP_STR.split('\n'):
        vals.append(input(s + '\n'))
    v1 = ','.join(vals)
    add_comp(conn, [v1])
    for s in menus.FIN_STR.split('\n'):
        vals.append(input(s + '\n'))
    v2 = ','.join([vals[0]] + vals[3:])
    add_fin(conn, [v2])
    print('Company created successfully!')


def upd_fin(data):
    sql = ''' UPDATE financial
                SET ebitda = ?,
                    sales = ?,
                    net_profit = ?,
                    market_price = ?,
                    net_debt = ?,
                    assets = ?,
                    equity = ?,
                    cash_equivalents = ?,
                    liabilities = ?    
                WHERE ticker = ? '''
    cur = conn.cursor()
    cur.execute(sql, data.split(','))
    conn.commit()


def add_comp(conn, data):
    sql = ''' INSERT INTO companies(ticker,name,sector) VALUES(?,?,?) '''
    cur = conn.cursor()
    for row in data:
        if '"' in row:
            row = row.replace(', Inc.', '_ Inc.')
            row = row.replace('"', '')
            row = row.split(',')
            for i in range(len(row)):
                row[i] = row[i].replace('_', ',')
        else:
            row = row.split(',')
        cur.execute(sql, row)
    conn.commit()


def add_fin(conn, data):
    sql = ''' INSERT INTO financial
                VALUES(?,?,?,?,?,?,?,?,?,?) '''
    cur = conn.cursor()
    for row in data:
        row = [x if x else None for x in row.split(',')]
        cur.execute(sql, row)
    conn.commit()


def read_data(path):
    data = []
    with open(path, 'r') as f:
        for line in f:
            data.append(line.rstrip())
    return data[1:]


def find_comp():
    mask = input('Enter company name:\n')
    mask = f"%{mask}%"
    sql = '''SELECT ticker, name FROM companies
                WHERE name LIKE ?'''
    cur = conn.cursor()
    res = cur.execute(sql, (mask,)).fetchall()
    comp = ''
    if res:
        for i in range(len(res)):
            print(i, res[i][1])
        num = input('Enter company number:\n')
        comp = res[int(num)]
    else:
        print('Company not found!')
    return comp


def upd_comp():
    comp = find_comp()
    if comp:
        vals = []
        for s in menus.FIN_STR.split('\n'):
            vals.append(input(s + '\n'))
        v = ','.join(vals + [comp[0]])
        upd_fin(v)
        print('Company updated successfully!')


def read_comp():
    comp = find_comp()
    # print(comp)
    if not comp:
        return
    sql = 'SELECT * FROM financial WHERE ticker=?'
    cur = conn.cursor()
    res = cur.execute(sql, (comp[0],)).fetchall()[0]
    print(comp[0], comp[1])
    print(f'P/E = {div(res[4], res[3])}')
    print(f'P/S = {div(res[4], res[2])}')
    print(f'P/B = {div(res[4], res[6])}')
    print(f'ND/EBITDA = {div(res[5], res[1])}')
    print(f'ROE = {div(res[3], res[7])}')
    print(f'ROA = {div(res[3], res[6])}')
    print(f'L/A = {div(res[9], res[6])}')


def div(a, b):
    return None if a is None or b is None else round(a / b, 2)


def del_comp():
    comp = find_comp()
    if comp:
        cur = conn.cursor()
        sql = 'DELETE FROM financial WHERE ticker=?'
        cur.execute(sql, (comp[0],))
        sql = 'DELETE FROM companies WHERE ticker=?'
        cur.execute(sql, (comp[0],))
        conn.commit()
        print('Company deleted successfully!')


def list_all():
    print('COMPANY LIST')
    sql = 'SELECT * FROM companies ORDER BY ticker'
    cur = conn.cursor()
    cur.execute(sql)
    for c in cur.fetchall():
        s = ''
        for w in c:
            s += w + ' '
        print(s.strip())


def list_top10(param):
    print(f'TICKER {param}')
    if param == 'ND/EBITDA':
        p1 = 'round(net_debt/ebitda, 2)'
        p2 = 'net_debt AND ebitda'
    elif param == 'ROE':
        p1 = 'round(net_profit/equity, 2)'
        p2 = 'net_profit AND equity'
    else:
        p1 = 'round(net_profit/assets, 2)'
        p2 = 'net_profit AND assets'
    sql = f'''SELECT ticker, {p1} as exp FROM financial WHERE {p2} NOT NULL ORDER by -exp'''
    cur = conn.cursor()
    cur.execute(sql)
    for c in cur.fetchmany(10):
        print(c[0], c[1])


def create_db():
    conn = sqlite3.connect('investor.db')
    count = create_tables(conn)
    if count < 10:
        data = read_data('test/companies.csv')
        add_comp(conn, data)
        data = read_data('test/financial.csv')
        add_fin(conn, data)
    return conn


def main():
    global conn
    conn = create_db()
    print('Welcome to the Investor Program!')
    main_menu()
    conn.close()


if __name__ == '__main__':
    main()
