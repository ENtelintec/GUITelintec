# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 05/jun./2024  at 16:37 $'

import pickle
import numpy as np
from keras.src.saving import load_model


def test_model_fichajes(filepath_model_class, filepath_scalar, filepath_out_vectors, day_of_week, month,
                        df=None, types_model=None, filepath_model_linear=None,
                        x_limits=((0, -2), (0, -2))):
    if types_model is None:
        types_model = [1, 2]
    if filepath_out_vectors is not None:
        with open(filepath_out_vectors, "rb") as f:
            data_out = pickle.load(f)
    elif df is not None:
        users = df["id_emp"].unique()
        print(users)
        data_out = []
        for emp in users:
            df_emp = df[(df["id_emp"] == emp) & (df["y"] == 1)]
            if len(df_emp) > 0:
                data_out.append(df_emp.iloc[-1].values)
            else:
                data_out.append([emp, 1, 1, 0, 0, 0, 0, 0, 0, 0])
        data_out = np.array(data_out)
        pathfile_out_vectors = "data/last_vals_lates.pkl"
        with open(pathfile_out_vectors, "wb") as f:
            pickle.dump(data_out, f)
    else:
        return [], [], "Error at reading data"
    # load scalar
    try:
        with open(filepath_scalar, "rb") as f:
            scalars = pickle.load(f)
        scalar_class = scalars[0]
        scalar_linear = scalars[1]
    except Exception as e:
        return [], [], f"Error at reading scalar: {str(e)}"
    # new instances where we do not know the answer
    rows = data_out.shape[0]
    for i in range(rows):
        data_out[i, 1] = day_of_week
        data_out[i, 2] = month
    xnew1 = data_out[:, x_limits[0][0]:x_limits[0][1]]
    xnew2 = data_out[:, x_limits[1][0]:x_limits[1][1]]
    xnew1 = scalar_class.transform(xnew1)
    xnew2 = scalar_linear.transform(xnew2)
    xnew = [xnew1, xnew2]
    # load model and evaluation
    y_news = []
    for item in types_model:
        match item:
            case 1:
                new_model_lates_class = load_model(filepath_model_class)
                y_news.append(new_model_lates_class.predict(xnew1))
            case 2:
                new_model_lates_linear = load_model(filepath_model_linear)
                y_news.append(new_model_lates_linear.predict(xnew2))
            case _:
                print("error type not admitted")
    return y_news, xnew, "Not error", data_out
