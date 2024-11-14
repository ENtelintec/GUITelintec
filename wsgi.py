# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 17/oct/2024  at 11:58 $"


from app import app

if __name__ == "__main__":
    app.run(host="192.168.1.73", port=5000, debug=True)
