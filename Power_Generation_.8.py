#!/usr/bin/env python
# coding: utf-8

#Variables:
#  Rad -
#    SWGDN surface shortwave flux
#  SLV - 
#    u2m eastward wind at 2m
#    v2m northward wind at 2m
#    u10m eastward wind at 10m
#    v10m northward wind at 10m
#    u50m eastward wind at 50m
#    v50m northward wind at 50m
#    T2M temperature at 2 m
#    PS surface pressure

#Wind output for one coordinate one year: 41 kbyte
#Total output storage: 41 kb / lat lon year * 40 years * 50 lat * 94 lon * 2 outputs (solar & wind)
#       15.4 Gbyte 

#Meeting:
# debug with julian file
# file restructure lat first; 0 --> (lat 0, lon 1); 1 --> (lat 0, lon 1)
# fall reflection, spring planning worksheet
# yearDay starts 0 --> whatever day in the file

#Questions:

#To-Do:
# explore julian file
# capacity value readings


import numpy as np
import os, sys, datetime
from netCDF4 import Dataset
import csv
import math
import PySAM.Pvwattsv5 as pv
import pandas as pd
import pvlib
import PySAM.Windpower as wp
import os.path
from os import path


def get_lat_lon(num_lats, num_lons, start_lat, start_lon):
    lat = np.arange(num_lats) * .5 + start_lat
    lon = np.arange(num_lons) * .625 + start_lon
    
    return lat, lon


def create_netCDF_files(year, lats, lons, destination):
    solar_name = destination + str(year) + "_solar_ac_generation.nc"
    solar = Dataset(solar_name, "w")
    lat = solar.createDimension("lat",lats.size)
    lon = solar.createDimension("lon",lons.size)
    hour = solar.createDimension("hour", 8760)
    solar_ac = solar.createVariable("ac","i4",("lat","lon","hour",))
    latitude = solar.createVariable("lat", "i4",("lat",))
    longitude = solar.createVariable("lon", "i4",("lon",))
    latitude[:] = lats
    longitude[:] = lons
    solar.close()
    
    
    wind_name = destination + str(year) + "_wind_ac_generation.nc"
    wind = Dataset(wind_name, "w")
    lat = wind.createDimension("lat",lats.size)
    lon = wind.createDimension("lon",lons.size)
    hour = wind.createDimension("hour", 8760)
    wind_ac = wind.createVariable("ac","i4",("lat","lon","hour",))
    latitude = solar.createVariable("lat", "i4",("lat",))
    longitude = solar.createVariable("lon", "i4",("lon",))
    latitude[:] = lats
    longitude[:] = lons
    wind.close()
    return 0


def create_csv(year, latitude, longitude): #lat lon in degrees
    csv_name = str(year) + '_' + str(latitude) + '_' + str(longitude) + '.csv'
    with open(csv_name, 'w', newline='') as csvfile:
        csvWriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        csvWriter.writerow(['Latitude']+['Longitude']+['Time Zone'])
        csvWriter.writerow([latitude]+[longitude]+[0])
        csvWriter.writerow(['Year']+['Month']+['Day']+['Hour']+['DNI']+['DHI']+['Wind Speed']+['Temperature'])
        csvfile.close()
    return csv_name


def create_srw(year, latitude, longitude): #lat lon in degrees
    srw_name = str(year) + '_' + str(latitude) + '_' + str(longitude) + '_wp.srw'
    with open(srw_name, 'w', newline='') as csvfile:
        csvWriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        csvWriter.writerow(['loc id=?']+['city=?']+['state=?']+['country=?']+[year]+[latitude]+[longitude]+['elevation=?']+[1]+[8760])
        csvWriter.writerow(['SAM wind power resource file'])
        csvWriter.writerow(['Temperature']+['Pressure']+['Speed']+['Speed']+['Speed']+['Direction'])
        csvWriter.writerow(['C']+['atm']+['m/s']+['m/s']+['m/s']+['degrees'])
        csvWriter.writerow(['2']+['2']+['2']+['10']+['50']+['50'])
        csvfile.close()
    return srw_name


def get_date(jd):
    
    daysInMonth = [0,31,59,90,120,151,181,212,243,273,304,334]
    for i in range(12):
        if jd > daysInMonth[i]:
            month = i + 1
    if jd > 31:
        day = jd % daysInMonth[month-1]
    else:
        day = jd
    return month, day      


def get_data(latitude, longitude, num_lons, merra_data):
    
    latLon = latitude * num_lons + longitude
    
    ghi = np.squeeze(np.array(merra_data.variables['SWGDN'][latLon, :, :]))
    ghi = ghi.reshape(ghi.size)
    v10m = np.squeeze(np.array(merra_data.variables['V10M'][latLon, :, :]))
    v10m = v10m.reshape(v10m.size)
    u2m = np.squeeze(np.array(merra_data.variables['U2M'][latLon, :, :]))
    u2m =u2m.reshape(u2m.size)
    v2m = np.squeeze(np.array(merra_data.variables['V2M'][latLon, :, :]))
    v2m = v2m.reshape(v2m.size)
    u10m = np.squeeze(np.array(merra_data.variables['U10M'][latLon, :, :]))
    u10m = u10m.reshape(u10m.size)
    v10m = np.squeeze(np.array(merra_data.variables['V10M'][latLon, :, :]))
    v10m = v10m.reshape(v10m.size)
    u50m = np.squeeze(np.array(merra_data.variables['U50M'][latLon, :, :]))
    u50m = u50m.reshape(u50m.size)
    v50m = np.squeeze(np.array(merra_data.variables['V50M'][latLon, :, :]))
    v50m = v50m.reshape(v50m.size)
    t2m = np.squeeze(np.array(merra_data.variables['T2M'][latLon, :, :]))
    t2m = t2m.reshape(t2m.size)
    pressure_Pa = np.squeeze(np.array(merra_data.variables['PS'][latLon, :, :]))
    pressure_Pa = pressure_Pa.reshape(pressure_Pa.size)
    
    pressure = pressure_Pa / 101325.0
    windSpeed2 = (v2m**2 + u2m**2)**.5
    windSpeed10 = (v10m**2 + u10m**2)**.5
    windSpeed50 = (v50m**2 + u50m**2)**.5
    windDirection = get_windDirection(u50m, v50m)
    temperature = (t2m - 273.15)
    
    return ghi, temperature, pressure, windSpeed2, windSpeed10, windSpeed50, windDirection 


def get_windDirection(u50m, v50m):
    
    direction = np.zeros(u50m.size)
    eastward = np.logical_and(u50m > 0, v50m != 0) 
    westward = np.logical_and(u50m < 0, v50m != 0)
    pure_northward = np.logical_and(u50m == 0, v50m > 0)
    pure_southward = np.logical_and(u50m == 0, v50m < 0)
    pure_eastward = np.logical_and(u50m > 0, v50m == 0)
    pure_westward = np.logical_and(u50m < 0, v50m == 0)
    direction[westward] = 90 - np.arctan(v50m[westward] / u50m[westward]) / np.pi * 180.
    direction[eastward] = 270 - np.arctan(v50m[eastward] / u50m[eastward]) / np.pi * 180.
    direction[pure_northward] = 180
    direction[pure_southward] = 0
    direction[pure_eastward] = 270
    direction[pure_westward] = 90
    return direction


def get_date_time_index(year, month, day):
    if day < 10:
        two_dig_day = ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09']
        str_day = two_dig_day[day]
    else:
        str_day = str(day)
    if month < 10:
        two_dig_month = ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09']
        str_month = two_dig_month[month]
    else:
        str_month = str(month)
    times = pd.date_range(str(year)+'-'+str_month+'-'+str_day, periods=24, freq='H')
    return times



def get_dni_dhi(year, jd, month, day, latitude, longitude, ghi):
    latitude_rads = latitude * 3.14159 / 180.0
    times = get_date_time_index(year, month, day)
    eqt = pvlib.solarposition.equation_of_time_pvcdrom(jd) # find 'equation of time' of given day (in minutes) 
    dec_rads = pvlib.solarposition.declination_spencer71(jd) # find 'solar declination' of given day (in radians)
    dec = dec_rads * 180. / np.pi # convert 'solar declination' (degrees)
    ha = np.array(pvlib.solarposition.hour_angle(times, longitude, eqt)) # find array of 'hour angles' for given day (in degrees)
    ha_rads = ha * np.pi / 180. # convert 'hour angle' (degrees)
    zen_rads = np.array(pvlib.solarposition.solar_zenith_analytical(latitude_rads, ha_rads, dec_rads)) # find array of 'zenith angles' for given day (in radians)
    zen = zen_rads * 180. / np.pi # convert 'zenith angles' (degrees)
    dni_temp = pvlib.irradiance.dirint(ghi, zen, times, pressure=None, use_delta_kt_prime=True, temp_dew=None, min_cos_zenith=0.0, max_zenith=90) #CHANGE
    dni = np.array(dni_temp.fillna(0)) #CHANGE
    dhi = ghi - dni * np.cos(zen_rads)
    return dni, dhi


def write_day2csv(csv_name, year, month, day, latitude, longitude, dni, dhi, windSpeed, temperature):
    with open(csv_name, 'a', newline='') as csvfile:
        for i in range(24):
            csvWriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            csvWriter.writerow([year]+[month]+[day]+[i]+[dni[i]]+[dhi[i]]+[windSpeed[i]]+[temperature[i]])
        csvfile.flush()
        csvfile.close()


def write_2srw(srw_name, temperature, pressure, windSpeed2, windSpeed10, windSpeed50, windDirection):
    with open(srw_name, 'a', newline='') as csvfile:
        for i in range(temperature.size):
            csvWriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            csvWriter.writerow([temperature[i]]+[pressure[i]]+[windSpeed2[i]]+[windSpeed10[i]]+[windSpeed50[i]]+[windDirection[i]])
        csvfile.flush()
        csvfile.close()


def run_solar(csv_name, file_path):
    d = pv.default("PVWattsNone")
    
    ##### Parameters #######
    
    d.SystemDesign.system_capacity = 1000   # System Capacity (kW)
    
    ########################
    d.LocationAndResource.solar_resource_file = file_path + csv_name
    d.execute()
    output_ac = np.array(d.Outputs.ac) / 1000000.
    
    return output_ac


def run_wp(csv_name, file_path):
    d = wp.default("WindPowerNone")
    
    ##### Parameters #######
    d.wind_resource_model_choice = 0
    d.WindTurbine.wind_turbine_hub_ht = 80
    d.WindFarm.system_capacity = 1000   # System Capacity (kW)
    
    ########################
    d.WindResourceFile.wind_resource_filename = file_path + csv_name
    d.execute()
    print("cf", d.Outputs.capacity_factor)
    output_ac = np.array(d.Outputs.gen) / 1000.
    
    return output_ac


def write_cord(year, solar_outputs, wind_outputs, lat, lon, destination):
    solar_name = destination + str(year) + "_solar_ac_generation.nc"
    solar = Dataset(solar_name, "a")
    solar_ac = solar.variables['ac']
    solar_ac[lat, lon, :] = solar_outputs
    solar.close()
    
    wind_name = destination + str(year) + "_wind_ac_generation.nc"
    wind = Dataset(wind_name, "a")
    wind_ac = wind.variables['ac']
    wind_ac[lat, lon, :] = wind_outputs
    wind.close()
    return 0


def main():
    
    ############## Program Parameters #############
    year = 2018
    start_lat = 31.5
    start_lon = -125
    num_lats = 37
    num_lons =  1 #31
    file_path = '/scratch/mtcraig_root/mtcraig/shared_data/westCoastYearFile/'            # Path to MERRA files
    file_name = 'cordDataWestCoastYear'                                                        #annual file name
    destination_file_path = '/scratch/mtcraig_root/mtcraig/shared_data/2018_west_coast_power_generation/'  #destination for power generation files
    ###############################################

    print('Begin Program: \t {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()))
    
    #get latitude and longitude arrays
    lat, lon = get_lat_lon(num_lats, num_lons, start_lat, start_lon) # (num lats, num lons, start lat, start lon)

    #check if output files exist
    solar_name = destination_file_path + str(year) + "_solar_ac_generation.nc"
    if path.exists(solar_name) == False:
        create_netCDF_files(year, lat, lon, destination_file_path)
    
    #find which longitude powGen script should access
    longitude = 0
    if path.exists("./log.txt"):
        l = open("./log.txt")
        for line in l:
            longitude = int(line) + 1
        l.close()

    #simulate power generation for every latitude
    for latitude in range(lat.size):
        csv_name = create_csv(year, lat[latitude], lon[longitude])
        srw_name = create_srw(year, lat[latitude], lon[longitude])
        
        merra_data = Dataset(file_path + file_name + '.nc')
        ghi, temperature, pressure, windSpeed2, windSpeed10, windSpeed50, windDirection = get_data(latitude, longitude, num_lons, merra_data)
        merra_data.close()
            
        write_2srw(srw_name, temperature, pressure, windSpeed2, windSpeed10, windSpeed50, windDirection)
        for jd in range(int(ghi.size / 24)):
            month, day = get_date(jd + 1)
            dni, dhi = get_dni_dhi(year, jd + 1, month, day, lat[latitude], lon[longitude], ghi[(jd)*24:(jd+1)*24]) #disc model
            write_day2csv(csv_name, year, month, day, lat[latitude], lon[longitude], dni, dhi, windSpeed2[(jd)*24:(jd+1)*24], temperature[(jd)*24:(jd+1)*24])
        solar_outputs = run_solar(csv_name, './')
        wind_outputs = run_wp(srw_name, './')
        
        os.remove(csv_name)
        os.remove(srw_name)
        write_cord(year, solar_outputs, wind_outputs, latitude, longitude, destination_file_path)
        print("%f, " %lat[latitude], "%f\t" %lon[longitude], '{:%Y-%m-%d %H:%M:%S} \n'.format(datetime.datetime.now()))
    l = open("./log.txt","a+")
    l.write("%d\n" %longitude)
    if longitude == num_lons - 1:
        l.write("done")
    l.close()
    print('Longitude finished: \t {:%Y-%m-%d %H:%M:%S} \n'.format(datetime.datetime.now()))

main()

