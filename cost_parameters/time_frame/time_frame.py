#Vehicle designs for different time frames

import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../..'))

import numpy as np
from gpkit import Model, ureg
from matplotlib import pyplot as plt
from aircraft_models import OnDemandAircraft 
from aircraft_models import OnDemandSizingMission, OnDemandRevenueMission
from aircraft_models import OnDemandDeadheadMission, OnDemandMissionCost
from study_input_data import generic_data, configuration_data
from collections import OrderedDict

#General data
eta_cruise = generic_data["\eta_{cruise}"] 
eta_electric = generic_data["\eta_{electric}"]
weight_fraction = generic_data["weight_fraction"]
C_m = generic_data["C_m"]
n = generic_data["n"]

reserve_type = generic_data["reserve_type"]
#autonomousEnabled = generic_data["autonomousEnabled"]
charger_power = generic_data["charger_power"]

#vehicle_cost_per_weight = generic_data["vehicle_cost_per_weight"]
battery_cost_per_C = generic_data["battery_cost_per_C"]
pilot_wrap_rate = generic_data["pilot_wrap_rate"]
mechanic_wrap_rate = generic_data["mechanic_wrap_rate"]
MMH_FH = generic_data["MMH_FH"]
#deadhead_ratio = generic_data["deadhead_ratio"]

#sizing_mission_type = generic_data["sizing_mission"]["type"]
sizing_N_passengers = generic_data["sizing_mission"]["N_passengers"]
sizing_mission_range = generic_data["sizing_mission"]["range"]
sizing_time_in_hover = generic_data["sizing_mission"]["time_in_hover"]

#revenue_mission_type = generic_data["revenue_mission"]["type"]
revenue_N_passengers = generic_data["revenue_mission"]["N_passengers"]
revenue_mission_range = generic_data["revenue_mission"]["range"]
revenue_time_in_hover = generic_data["revenue_mission"]["time_in_hover"]

#deadhead_mission_type = generic_data["deadhead_mission"]["type"]
deadhead_N_passengers = generic_data["deadhead_mission"]["N_passengers"]
deadhead_mission_range = generic_data["deadhead_mission"]["range"]
deadhead_time_in_hover = generic_data["deadhead_mission"]["time_in_hover"]


# Data specific to study
configs = {}
time_frame_array = ["Initial","Near term","Long term"]

time_frame_data = {}
time_frame_data["Initial"] = {}
time_frame_data["Near term"] = {}
time_frame_data["Long term"] = {}

time_frame_data["Initial"]["autonomousEnabled"] = False
time_frame_data["Near term"]["autonomousEnabled"] = True
time_frame_data["Long term"]["autonomousEnabled"] = True

time_frame_data["Initial"]["sizing_mission_type"] = "piloted"
time_frame_data["Near term"]["sizing_mission_type"] = "piloted"
time_frame_data["Long term"]["sizing_mission_type"] = "piloted"

time_frame_data["Initial"]["revenue_mission_type"] = "piloted"
time_frame_data["Near term"]["revenue_mission_type"] = "piloted"
time_frame_data["Long term"]["revenue_mission_type"] = "autonomous"

time_frame_data["Initial"]["deadhead_mission_type"] = "piloted"
time_frame_data["Near term"]["deadhead_mission_type"] = "autonomous"
time_frame_data["Long term"]["deadhead_mission_type"] = "autonomous"

time_frame_data["Initial"]["deadhead_ratio"] = 0.5
time_frame_data["Near term"]["deadhead_ratio"] = 0.35
time_frame_data["Long term"]["deadhead_ratio"] = 0.2

time_frame_data["Initial"]["vehicle_cost_per_weight"] = 600*ureg.lbf**-1
time_frame_data["Near term"]["vehicle_cost_per_weight"] = 400*ureg.lbf**-1
time_frame_data["Long term"]["vehicle_cost_per_weight"] = 200*ureg.lbf**-1

time_frame_data["Initial"]["C_m"] = 300*ureg.Wh/ureg.kg
time_frame_data["Near term"]["C_m"] = 400*ureg.Wh/ureg.kg
time_frame_data["Long term"]["C_m"] = 500*ureg.Wh/ureg.kg

time_frame_data["Initial"]["battery_cost_per_C"] = 400*ureg.kWh**-1
time_frame_data["Near term"]["battery_cost_per_C"] = 200*ureg.kWh**-1
time_frame_data["Long term"]["battery_cost_per_C"] = 100*ureg.kWh**-1


for config in configuration_data:
	configs[config] = OrderedDict()
	for time_frame in time_frame_array:
		configs[config][time_frame] = configuration_data[config].copy()

#Delete unwanted configurations
del configs["Multirotor"]
del configs["Autogyro"]
del configs["Tilt duct"]
del configs["Helicopter"]

#Optimize remaining configurations
for config in configs:
	
	print "Solving configuration: " + config

	for time_frame in configs[config]:
		
		c = configs[config][time_frame]

		V_cruise = c["V_{cruise}"]
		L_D_cruise = c["L/D"]
		T_A = c["T/A"]
		Cl_mean_max = c["Cl_{mean_{max}}"]
		N = c["N"]

		autonomousEnabled = time_frame_data[time_frame]["autonomousEnabled"]
		sizing_mission_type = time_frame_data[time_frame]["sizing_mission_type"]
		revenue_mission_type = time_frame_data[time_frame]["revenue_mission_type"]
		deadhead_mission_type = time_frame_data[time_frame]["deadhead_mission_type"]
		deadhead_ratio = time_frame_data[time_frame]["deadhead_ratio"]
		
		vehicle_cost_per_weight = time_frame_data[time_frame]["vehicle_cost_per_weight"]
		C_m = time_frame_data[time_frame]["C_m"]
		battery_cost_per_C = time_frame_data[time_frame]["battery_cost_per_C"]

		Aircraft = OnDemandAircraft(N=N,L_D_cruise=L_D_cruise,eta_cruise=eta_cruise,C_m=C_m,
			Cl_mean_max=Cl_mean_max,weight_fraction=weight_fraction,n=n,eta_electric=eta_electric,
			cost_per_weight=vehicle_cost_per_weight,cost_per_C=battery_cost_per_C,
			autonomousEnabled=autonomousEnabled)

		SizingMission = OnDemandSizingMission(Aircraft,mission_range=sizing_mission_range,
			V_cruise=V_cruise,N_passengers=sizing_N_passengers,time_in_hover=sizing_time_in_hover,
			reserve_type=reserve_type,mission_type=sizing_mission_type)
		SizingMission.substitutions.update({SizingMission.fs0.topvar("T/A"):T_A})
	
		RevenueMission = OnDemandRevenueMission(Aircraft,mission_range=revenue_mission_range,
			V_cruise=V_cruise,N_passengers=revenue_N_passengers,time_in_hover=revenue_time_in_hover,
			charger_power=charger_power,mission_type=revenue_mission_type)

		DeadheadMission = OnDemandDeadheadMission(Aircraft,mission_range=deadhead_mission_range,
			V_cruise=V_cruise,N_passengers=deadhead_N_passengers,time_in_hover=deadhead_time_in_hover,
			charger_power=charger_power,mission_type=deadhead_mission_type)

		MissionCost = OnDemandMissionCost(Aircraft,RevenueMission,DeadheadMission,
			pilot_wrap_rate=pilot_wrap_rate,mechanic_wrap_rate=mechanic_wrap_rate,MMH_FH=MMH_FH,
			deadhead_ratio=deadhead_ratio)
	
		problem = Model(MissionCost["cost_per_trip"],
			[Aircraft, SizingMission, RevenueMission, DeadheadMission, MissionCost])
	
		solution = problem.solve(verbosity=0)

		configs[config][time_frame]["solution"] = solution

		configs[config][time_frame]["MTOW"] = solution("MTOW_OnDemandAircraft")
		configs[config][time_frame]["W_{battery}"] = solution("W_OnDemandAircraft/Battery")
		configs[config][time_frame]["cost_per_trip_per_passenger"] = solution("cost_per_trip_per_passenger_OnDemandMissionCost")
		configs[config][time_frame]["SPL"] = 20*np.log10(solution("p_{ratio}_OnDemandSizingMission"))

		c_vehicle = solution("purchase_price_OnDemandAircraft")
		c_avionics = solution("purchase_price_OnDemandAircraft/Avionics")
		c_battery = solution("purchase_price_OnDemandAircraft/Battery")
		configs[config][time_frame]["purchase_price"] = c_vehicle + c_avionics + c_battery

		NdNr = solution("N_{deadhead}/N_{typical}_OnDemandMissionCost")
		configs[config][time_frame]["NdNr"] = NdNr

		amortized_pilot_cost_revenue = solution("cost_per_mission_OnDemandMissionCost/RevenueMissionCost/OperatingExpenses/PilotCost")
		amortized_pilot_cost_deadhead = solution("cost_per_mission_OnDemandMissionCost/DeadheadMissionCost/OperatingExpenses/PilotCost")
		configs[config][time_frame]["amortized_capex_revenue"] = amortized_pilot_cost_revenue
		configs[config][time_frame]["amortized_capex_deadhead"] = amortized_pilot_cost_deadhead
		configs[config][time_frame]["amortized_pilot_cost"] = amortized_pilot_cost_revenue + amortized_pilot_cost_deadhead

		amortized_capex_revenue = solution("cost_per_mission_OnDemandMissionCost/RevenueMissionCost/CapitalExpenses")
		amortized_capex_deadhead = NdNr*solution("cost_per_mission_OnDemandMissionCost/DeadheadMissionCost/CapitalExpenses")
		configs[config][time_frame]["amortized_capex_revenue"] = amortized_capex_revenue
		configs[config][time_frame]["amortized_capex_deadhead"] = amortized_capex_deadhead
		configs[config][time_frame]["amortized_capex"] = amortized_capex_revenue + amortized_capex_deadhead

		amortized_opex_revenue = solution("cost_per_mission_OnDemandMissionCost/RevenueMissionCost/OperatingExpenses")
		amortized_opex_deadhead = NdNr*solution("cost_per_mission_OnDemandMissionCost/DeadheadMissionCost/OperatingExpenses")
		configs[config][time_frame]["amortized_opex_revenue"] = amortized_opex_revenue
		configs[config][time_frame]["amortized_opex_deadhead"] = amortized_opex_deadhead
		configs[config][time_frame]["amortized_opex"] = amortized_opex_revenue + amortized_opex_deadhead


# Plotting commands
plt.ion()
fig1 = plt.figure(figsize=(12,12), dpi=80)
plt.rc('axes', axisbelow=True)
plt.show()

y_pos = np.arange(len(configs))
labels = [""]*len(configs)
for i, config in enumerate(configs):
	labels[i] = config

offset_array = [-0.3,0,0.3]
width = 0.2
colors = ["grey", "w", "k"]

#Maximum takeoff weight
plt.subplot(2,2,1)
for i,config in enumerate(configs):
	for j,time_frame in enumerate(configs[config]):
		c = configs[config][time_frame]
		offset = offset_array[j]
		MTOW = c["MTOW"].to(ureg.lbf).magnitude

		if (i == 0):
			label = time_frame
			plt.bar(i+offset,MTOW,align='center',alpha=1,width=width,color=colors[j],
				label=label)
		else:
			plt.bar(i+offset,MTOW,align='center',alpha=1,width=width,color=colors[j])

plt.grid()
plt.xticks(y_pos, labels, rotation=-45, fontsize=12)
plt.ylabel('Weight (lbf)', fontsize = 16)
plt.title("Maximum Takeoff Weight",fontsize = 18)
plt.legend(loc='upper right', fontsize = 12)


#Battery weight
plt.subplot(2,2,2)
for i,config in enumerate(configs):
	for j,time_frame in enumerate(configs[config]):
		c = configs[config][time_frame]
		offset = offset_array[j]
		W_battery = c["W_{battery}"].to(ureg.lbf).magnitude

		if (i == 0):
			label = time_frame
			plt.bar(i+offset,W_battery,align='center',alpha=1,width=width,color=colors[j],
				label=label)
		else:
			plt.bar(i+offset,W_battery,align='center',alpha=1,width=width,color=colors[j])

plt.grid()
plt.xticks(y_pos, labels, rotation=-45, fontsize=12)
plt.ylabel('Weight (lbf)', fontsize = 16)
plt.title("Battery Weight",fontsize = 18)
plt.legend(loc='upper right', fontsize = 12)


#Trip cost per passenger 
plt.subplot(2,2,3)
for i,config in enumerate(configs):
	for j,time_frame in enumerate(configs[config]):
		c = configs[config][time_frame]
		offset = offset_array[j]
		cptpp = c["cost_per_trip_per_passenger"]

		if (i == 0):
			label = time_frame
			plt.bar(i+offset,cptpp,align='center',alpha=1,width=width,color=colors[j],
				label=label)
		else:
			plt.bar(i+offset,cptpp,align='center',alpha=1,width=width,color=colors[j])

plt.grid()
plt.xticks(y_pos, labels, rotation=-45, fontsize=12)
plt.ylabel('Cost ($US)', fontsize = 16)
plt.title("Cost per Trip, per Passenger",fontsize = 18)
plt.legend(loc='upper right', fontsize = 12)


#Sound pressure level (in hover) 
plt.subplot(2,2,4)
for i,config in enumerate(configs):
	for j,time_frame in enumerate(configs[config]):
		c = configs[config][time_frame]
		offset = offset_array[j]
		SPL_sizing = c["SPL"]

		if (i == 0):
			label = time_frame
			plt.bar(i+offset,SPL_sizing,align='center',alpha=1,width=width,color=colors[j],
				label=label)
		else:
			plt.bar(i+offset,SPL_sizing,align='center',alpha=1,width=width,color=colors[j])

SPL_req = 62
plt.plot([np.min(y_pos)-1,np.max(y_pos)+1],[SPL_req, SPL_req],
	color="black", linewidth=3, linestyle="-")
plt.ylim(ymin = 57,ymax = 85)
plt.grid()
plt.xticks(y_pos, labels, rotation=-45, fontsize=12)
plt.ylabel('SPL (dB)', fontsize = 16)
plt.title("Sound Pressure Level in Hover",fontsize = 18)
plt.legend(loc='upper right', fontsize = 12)


if autonomousEnabled:
	autonomy_string = "autonomy enabled"
else:
	autonomy_string = "pilot required"

title_str = "Aircraft parameters: structural mass fraction = %0.2f\n" % weight_fraction \
	+ "Sizing mission: range = %0.0f nm; %0.0f passengers; %0.0fs hover time\n" \
	% (sizing_mission_range.to(ureg.nautical_mile).magnitude, sizing_N_passengers,\
		sizing_time_in_hover.to(ureg.s).magnitude) \
	+ "Revenue mission: range = %0.0f nm; %0.1f passengers; %0.0fs hover time; no reserve; charger power = %0.0f kW\n" \
	% (revenue_mission_range.to(ureg.nautical_mile).magnitude, \
		revenue_N_passengers, revenue_time_in_hover.to(ureg.s).magnitude, charger_power.to(ureg.kW).magnitude) \
	+ "Deadhead mission: range = %0.0f nm; %0.1f passengers; %0.0fs hover time; no reserve" \
	% (deadhead_mission_range.to(ureg.nautical_mile).magnitude, \
		deadhead_N_passengers, deadhead_time_in_hover.to(ureg.s).magnitude)

plt.suptitle(title_str,fontsize = 14)

plt.tight_layout()#makes sure subplots are spaced neatly
plt.subplots_adjust(left=0.07,right=0.99,bottom=0.10,top=0.88)#adds space at the top for the title


#Cost breakdown plot
fig2 = plt.figure(figsize=(12,12), dpi=80)
plt.show()

#Vehicle acquisition cost
plt.subplot(2,2,1)
for i,config in enumerate(configs):
	for j,time_frame in enumerate(configs[config]):
		c = configs[config][time_frame]
		offset = offset_array[j]
		purchase_price = c["purchase_price"]/1e6
		if (i == 0):
			label = time_frame
			plt.bar(i+offset,purchase_price,align='center',alpha=1,width=width,
				color=colors[j],label=label)
		else:
			plt.bar(i+offset,purchase_price,align='center',alpha=1,width=width,color=colors[j])

plt.grid()
plt.xticks(y_pos, labels, rotation=-45, fontsize=12)
plt.ylabel('Cost ($millions US)', fontsize = 16)
plt.title("Vehicle Acquisition Cost",fontsize = 18)
plt.legend(loc='upper right', fontsize = 12)

#Pilot cost per mission
plt.subplot(2,2,2)
for i,config in enumerate(configs):
	for j,time_frame in enumerate(configs[config]):
		c = configs[config][time_frame]
		offset = offset_array[j]
		pilot_cost = c["amortized_pilot_cost"]
		if (i == 0):
			label = time_frame
			plt.bar(i+offset,pilot_cost,align='center',alpha=1,width=width,color=colors[j],
				label=label)
		else:
			plt.bar(i+offset,pilot_cost,align='center',alpha=1,width=width,color=colors[j])

plt.grid()
plt.xticks(y_pos, labels, rotation=-45, fontsize=12)
plt.ylabel('Cost ($US)', fontsize = 16)
plt.title("Pilot Cost per Trip",fontsize = 18)
plt.legend(loc='upper right', fontsize = 12)

#Amortized capital expenses per mission
plt.subplot(2,2,3)
for i,config in enumerate(configs):
	for j,time_frame in enumerate(configs[config]):
		c = configs[config][time_frame]
		offset = offset_array[j]
		amortized_capex = c["amortized_capex"]
		if (i == 0):
			label = time_frame
			plt.bar(i+offset,amortized_capex,align='center',alpha=1,width=width,
				color=colors[j],label=label)
		else:
			plt.bar(i+offset,amortized_capex,align='center',alpha=1,width=width,color=colors[j])

plt.grid()
plt.xticks(y_pos, labels, rotation=-45, fontsize=12)
plt.ylabel('Cost ($US)', fontsize = 16)
plt.title("Capital Expenses per Trip",fontsize = 18)
plt.legend(loc='upper right', fontsize = 12)

#Amortized operating expenses per mission
plt.subplot(2,2,4)
for i,config in enumerate(configs):
	for j,time_frame in enumerate(configs[config]):
		c = configs[config][time_frame]
		offset = offset_array[j]
		amortized_opex = c["amortized_opex"]

		if (i == 0):
			label = time_frame
			plt.bar(i+offset,amortized_opex,align='center',alpha=1,width=width,
				color=colors[j],label=label)
		else:
			plt.bar(i+offset,amortized_opex,align='center',alpha=1,width=width,color=colors[j])

plt.grid()
plt.xticks(y_pos, labels, rotation=-45, fontsize=12)
plt.ylabel('Cost ($US)', fontsize = 16)
plt.title("Operating Expenses per Trip",fontsize = 18)
plt.legend(loc='upper right', fontsize = 12)

plt.suptitle(title_str,fontsize = 14)

plt.tight_layout()#makes sure subplots are spaced neatly
plt.subplots_adjust(left=0.07,right=0.99,bottom=0.10,top=0.88)#adds space at the top for the title