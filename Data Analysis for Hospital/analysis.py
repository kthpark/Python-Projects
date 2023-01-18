import pandas as pd
import numpy as np

import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('TkAgg')


def create_patients_df(df_hospital, df_prenatal, df_sports):
    df_prenatal.columns = df_hospital.columns
    df_sports.columns = df_hospital.columns

    patient = pd.concat([df_hospital, df_prenatal, df_sports], ignore_index=True)

    patient.drop(columns=['Unnamed: 0'], inplace=True)
    patient.dropna(axis=0, how='all', inplace=True)

    patient['gender'].replace(
        ['female', 'male', 'man', 'woman'],
        ['f', 'm', 'm', 'f'],
        inplace=True
    )

    patient['gender'].replace(np.nan, 'f', inplace=True)

    columns = ['bmi', 'diagnosis', 'blood_test', 'ecg', 'ultrasound', 'mri', 'xray', 'children', 'months']
    for i in columns:
        patient[i] = patient[i].replace(np.nan, 0)

    return patient


def display_df(patient):
    print(patient.sample(n=len(patient)))

    patient.plot(title='Distribution of patients by age.', y='age', kind='hist', bins=range(0, 80))
    plt.show()

    patient.diagnosis.value_counts().plot(title='Distribution of patients by diagnosis.', kind='pie')
    plt.show()

    axis = plt.subplots()[1]
    axis.set_title('Distribution of patients by height.')
    plt.violinplot(patient['height'])
    plt.show()


if __name__ == '__main__':
    pd.set_option('display.max_columns', 8)

    df_gen = pd.read_csv('general.csv')
    df_pre = pd.read_csv('prenatal.csv')
    df_spo = pd.read_csv('sports.csv')

    patients = create_patients_df(df_gen, df_pre, df_spo)

    display_df(patients)
