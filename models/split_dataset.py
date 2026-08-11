# data_preparation.py
import argparse

import pandas as pd
from sklearn.model_selection import train_test_split


def load_data(file_path):
    df = pd.read_csv(file_path)
    df["status"]
    return df


def split_and_save_data(
    data, train_A_path, train_B_path, test_path, test_size=0.2, split_ratio=0.5
):
    train_val_set, test_set = train_test_split(
        data, test_size=test_size, random_state=42
    )
    train_set_A, train_set_B = train_test_split(
        train_val_set, test_size=split_ratio, random_state=42
    )
    train_set_A.to_csv(train_A_path, index=False)
    train_set_B.to_csv(train_B_path, index=False)
    test_set.to_csv(test_path, index=False)


if __name__ == "__main__":
   
    args = parser.parse_args()

    data = load_data(args.input_file)
    split_and_save_data(data, args.train_A_file, args.train_B_file, args.test_file)
