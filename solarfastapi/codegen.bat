@echo off
title First
sqlacodegen sqlite:///test_data.db > autosqla.py
pause