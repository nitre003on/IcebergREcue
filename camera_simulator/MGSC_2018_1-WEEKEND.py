import math
print('pls enter startdate....')
startdate = list(input())
print('pls enter enddate....')
enddate = list(input())
Day_1 = int(startdate[0])*10 + int(startdate[1])
Day_2 = int(enddate[0])*10 + int(enddate[1])
Month_1 = int(startdate[3])*10 + int(startdate[4])
Month_2 = int(enddate[3])*10 + int(enddate[4])
Year_1 = int(startdate[6])*1000 + int(startdate[7])*100 + int(startdate[8])*10 + int(startdate[9])
Year_2 = int(enddate[6])*1000 + int(enddate[7])*100 + int(enddate[8])*10 + int(enddate[9]) 
actual_year_1 =  Year_1 - 1900
actual_year_2 =  Year_2 - 1900
DY1 = actual_year_1*365 + math.floor(actual_year_1/4)
DY2 = actual_year_2*365 + math.floor(actual_year_2/4)
def DM1():
    if Month_1 == 1:
        Dm1 = 0
    elif Month_1 == 2:
        Dm1 = 31
    elif Month_1 == 3:
        Dm1 = 59
    elif Month_1 == 4:
        Dm1 = 90
    elif Month_1 == 5:
        Dm1 = 120
    elif Month_1 == 6:
        Dm1 = 151
    elif Month_1 == 7:
        Dm1 = 181
    elif Month_1 == 8:
        Dm1 = 212
    elif Month_1 == 9:
        Dm1 = 243
    elif Month_1 == 10:
        Dm1 = 273
    elif Month_1 == 11:
        Dm1 = 304
    elif Month_1 == 12:
        Dm1 = 334
    return(Dm1)
Dm1 = DM1()
def DM2():
    if Month_2 == 1:
        Dm2 = 0
    elif Month_2 == 2:
        Dm2 = 31
    elif Month_2 == 3:
        Dm2 = 59
    elif Month_2 == 4:
        Dm2 = 90
    elif Month_2 == 5:
        Dm2 = 120
    elif Month_2 == 6:
        Dm2 = 151
    elif Month_2 == 7:
        Dm2 = 181
    elif Month_2 == 8:
        Dm2 = 212
    elif Month_2 == 9:
        Dm2 = 243
    elif Month_2 == 10:
        Dm2 = 273
    elif Month_2 == 11:
        Dm2 = 304
    elif Month_2 == 12:
        Dm2 = 334
    return(Dm2)
Dm2 = DM2()
D1T = DY1 + Dm1 + Day_1
D2T = DY2 + Dm2 + Day_2
DT = D2T - D1T
weekstotal = round(DT/7)
print(weekstotal)