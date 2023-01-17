import pandas as pd

if __name__ == '__main__':

    df_a, df_b, df_hr = pd.read_xml('A_office_data.xml'), pd.read_xml('B_office_data.xml'), pd.read_xml('hr_data.xml')

    df_a.index = df_a.employee_office_id.apply(lambda x: "A" + str(x))
    df_b.index = df_b.employee_office_id.apply(lambda x: "B" + str(x))
    df_hr.set_index("employee_id", inplace=True, drop=False)

    df = (
        pd.concat([df_a, df_b], axis=0)
        .merge(df_hr, left_index=True, right_index=True, indicator=True)
        .drop(["employee_office_id", "employee_id", "_merge"], axis=1)
        .sort_index()
    )

    merge_piv = pd.pivot_table(
        df,
        index="Department",
        columns=["left", "salary"],
        values="average_monthly_hours",
        aggfunc="median",
    )

    print(
        merge_piv[(merge_piv[0, "high"] < merge_piv[0, "medium"]) | (merge_piv[1, "low"] < merge_piv[1, "high"])]
        .round(2)
        .to_dict()
    )

    time_spent_piv = pd.pivot_table(
        df,
        index="time_spend_company",
        columns="promotion_last_5years",
        values=["satisfaction_level", "last_evaluation"],
        aggfunc=["min", "max", "mean"],
    )

    print(
        time_spent_piv[time_spent_piv["mean", "last_evaluation", 0] > time_spent_piv["mean", "last_evaluation", 1]]
        .round(2)
        .to_dict()
    )
