#CGenerate carpet plot for vehicle sizing

import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/' + '..'))

import numpy as np
from gpkit import Model, ureg
from matplotlib import pyplot as plt
from aircraft_models import OnDemandAircraft 
from aircraft_models import OnDemandSizingMission, OnDemandRevenueMission
from aircraft_models import OnDemandDeadheadMission, OnDemandMissionCost
from study_input_data import generic_data, configuration_data


#General data
eta_cruise = generic_data["\eta_{cruise}"] 
eta_electric = generic_data["\eta_{electric}"]
weight_fraction = generic_data["weight_fraction"]
C_m = generic_data["C_m"]
n = generic_data["n"]

reserve_type = generic_data["reserve_type"]
autonomousEnabled = generic_data["autonomousEnabled"]
charger_power = generic_data["charger_power"]

vehicle_cost_per_weight = generic_data["vehicle_cost_per_weight"]
battery_cost_per_C = generic_data["battery_cost_per_C"]
pilot_wrap_rate = generic_data["pilot_wrap_rate"]
mechanic_wrap_rate = generic_data["mechanic_wrap_rate"]
MMH_FH = generic_data["MMH_FH"]
deadhead_ratio = generic_data["deadhead_ratio"]

sizing_mission_type = generic_data["sizing_mission"]["type"]
sizing_N_passengers = generic_data["sizing_mission"]["N_passengers"]
sizing_mission_range = generic_data["sizing_mission"]["range"]
sizing_t_hover = generic_data["sizing_mission"]["t_{hover}"]

revenue_mission_type = generic_data["revenue_mission"]["type"]
revenue_N_passengers = generic_data["revenue_mission"]["N_passengers"]
revenue_mission_range = generic_data["revenue_mission"]["range"]
revenue_t_hover = generic_data["revenue_mission"]["t_{hover}"]

deadhead_mission_type = generic_data["deadhead_mission"]["type"]
deadhead_N_passengers = generic_data["deadhead_mission"]["N_passengers"]
deadhead_mission_range = generic_data["deadhead_mission"]["range"]
deadhead_t_hover = generic_data["deadhead_mission"]["t_{hover}"]

numrows = 10
L_D_array = np.linspace(10,14,numrows)
T_A_array = np.linspace(4.5,14,numrows)
L_D_array, T_A_array = np.meshgrid(L_D_array, T_A_array)
T_A_array = T_A_array*ureg.lbf/ureg.ft**2

cptpp = np.zeros(np.shape(L_D_array))
SPL = np.zeros(np.shape(L_D_array))

#Optimize 
configs = configuration_data.copy()
config = "Tilt rotor" #pull other data from this configuration
c = configs[config]


for i, T_A in enumerate(T_A_array[:,0]):
	for j, L_D_cruise in enumerate(L_D_array[0]):
		
		V_cruise = c["V_{cruise}"]
		Cl_mean_max = c["Cl_{mean_{max}}"]
		N = c["N"]
		loiter_type = c["loiter_type"]

		Aircraft = OnDemandAircraft(N=N,L_D_cruise=L_D_cruise,eta_cruise=eta_cruise,C_m=C_m,
			Cl_mean_max=Cl_mean_max,weight_fraction=weight_fraction,n=n,eta_electric=eta_electric,
			cost_per_weight=vehicle_cost_per_weight,cost_per_C=battery_cost_per_C,
			autonomousEnabled=autonomousEnabled)

		SizingMission = OnDemandSizingMission(Aircraft,mission_range=sizing_mission_range,
			V_cruise=V_cruise,N_passengers=sizing_N_passengers,t_hover=sizing_t_hover,
			reserve_type=reserve_type,mission_type=sizing_mission_type,loiter_type=loiter_type)
		SizingMission.substitutions.update({SizingMission.fs0.topvar("T/A"):T_A})
	
		RevenueMission = OnDemandRevenueMission(Aircraft,mission_range=revenue_mission_range,
			V_cruise=V_cruise,N_passengers=revenue_N_passengers,t_hover=revenue_t_hover,
			charger_power=charger_power,mission_type=revenue_mission_type)

		DeadheadMission = OnDemandDeadheadMission(Aircraft,mission_range=deadhead_mission_range,
			V_cruise=V_cruise,N_passengers=deadhead_N_passengers,t_hover=deadhead_t_hover,
			charger_power=charger_power,mission_type=deadhead_mission_type)

		MissionCost = OnDemandMissionCost(Aircraft,RevenueMission,DeadheadMission,
			pilot_wrap_rate=pilot_wrap_rate,mechanic_wrap_rate=mechanic_wrap_rate,MMH_FH=MMH_FH,
			deadhead_ratio=deadhead_ratio)
	
		problem = Model(MissionCost["cost_per_trip"],
			[Aircraft, SizingMission, RevenueMission, DeadheadMission, MissionCost])
	
		solution = problem.solve(verbosity=0)

		cptpp[i,j] = solution("cost_per_trip_per_passenger_OnDemandMissionCost")
		SPL[i,j] = 20*np.log10(solution("p_{ratio}_OnDemandSizingMission")[0])



# Plotting commands
plt.ion()
fig1 = plt.figure(figsize=(12,12), dpi=80)
plt.rc('axes', axisbelow=True)
plt.show()
cptpp_plot = plt.contour(L_D_array, T_A_array.to(ureg.lbf/ureg.ft**2).magnitude, cptpp, 
	colors='black')
plt.clabel(cptpp_plot,fontsize=16,fmt="$%1.0f US")
SPL_plot = plt.contour(L_D_array, T_A_array.to(ureg.lbf/ureg.ft**2).magnitude, SPL, 
	colors='black')
plt.clabel(SPL_plot,fontsize=16,fmt="%1.0f dB")
plt.xlabel('Lift-to-Drag Ratio',fontsize = 20)
plt.ylabel('Disk loading $(lbf/ft^2)$',fontsize = 20)



if reserve_type == "FAA_day" or reserve_type == "FAA_night":
	num = solution("t_{loiter}_OnDemandSizingMission").to(ureg.minute).magnitude
	if reserve_type == "FAA_day":
		reserve_type_string = "FAA day VFR (%0.0f-minute loiter time)" % num
	elif reserve_type == "FAA_night":
		reserve_type_string = "FAA night VFR (%0.0f-minute loiter time)" % num
elif reserve_type == "Uber":
	num = solution["constants"]["R_{divert}_OnDemandSizingMission"].to(ureg.nautical_mile).magnitude
	reserve_type_string = " (%0.0f-nm diversion distance)" % num

if autonomousEnabled:
	autonomy_string = "autonomy enabled"
else:
	autonomy_string = "pilot required"

title_str = "Aircraft parameters: structural mass fraction = %0.2f; battery energy density = %0.0f Wh/kg; %s\n" \
	% (weight_fraction, C_m.to(ureg.Wh/ureg.kg).magnitude, autonomy_string) \
	+ "Sizing mission (%s): range = %0.0f nm; %0.0f passengers; %0.0fs hover time; reserve type = " \
	% (sizing_mission_type, sizing_mission_range.to(ureg.nautical_mile).magnitude, sizing_N_passengers, sizing_t_hover.to(ureg.s).magnitude) \
	+ reserve_type_string + "\n"\
	+ "Revenue mission (%s): range = %0.0f nm; %0.1f passengers; %0.0fs hover time; no reserve; charger power = %0.0f kW\n" \
	% (revenue_mission_type, revenue_mission_range.to(ureg.nautical_mile).magnitude, \
		revenue_N_passengers, revenue_t_hover.to(ureg.s).magnitude, charger_power.to(ureg.kW).magnitude) \
	+ "Deadhead mission (%s): range = %0.0f nm; %0.1f passengers; %0.0fs hover time; no reserve; deadhead ratio = %0.1f" \
	% (deadhead_mission_type, deadhead_mission_range.to(ureg.nautical_mile).magnitude, \
		deadhead_N_passengers, deadhead_t_hover.to(ureg.s).magnitude, deadhead_ratio)


plt.title(title_str,fontsize = 13.5, y = 1.02)
plt.tight_layout()
plt.subplots_adjust(left=0.07,right=0.94,bottom=0.07,top=0.9)
plt.savefig('sizing_plot_01.pdf')

'''
#Additional parameters plot
fig2 = plt.figure(figsize=(12,12), dpi=80)
plt.show()

offset_array = [-0.3,0,0.3]
width = 0.2
colors = ["grey", "w", "k"]

#Energy use by mission segment (sizing mission)
plt.subplot(2,2,1)
for i, config in enumerate(configs):
	sol = configs[config]["solution"]

	E_data = [dict() for x in range(3)]	
	
	E_data[0]["type"] = "Cruise"
	E_data[0]["value"] = sol("E_OnDemandSizingMission")[1]
	
	E_data[1]["type"] = "Hover"
	E_data[1]["value"] = sol("E_OnDemandSizingMission")[0]
	E_data[1]["value"] = E_data[1]["value"]*4 #number of hover segments

	E_data[2]["type"] = "Reserve"
	E_data[2]["value"] = sol("E_OnDemandSizingMission")[4]

	bottom = 0
	for j,E in enumerate(E_data):
		E_value = E["value"].to(ureg.kWh).magnitude
		if (i == 0):
			plt.bar(i,E_value,align='center',bottom=bottom,alpha=1,color=colors[j],
				label=E["type"])
		else:
			plt.bar(i,E_value,align='center',bottom=bottom,alpha=1,color=colors[j])
		bottom = bottom + E_value

plt.grid()
plt.xticks(y_pos, labels, rotation=-45, fontsize=12)
plt.ylabel('Energy (kWh)', fontsize = 16)
plt.title("Energy Use",fontsize = 18)
plt.legend(loc='upper right', fontsize = 12)


#Power consumption by mission segment (sizing mission)
plt.subplot(2,2,2)
for i, config in enumerate(configs):
	sol = configs[config]["solution"]

	P_battery = np.zeros(3)	
	P_battery[0] = sol("P_{battery}_OnDemandSizingMission")[1].to(ureg.kW).magnitude#cruise
	P_battery[1] = sol("P_{battery}_OnDemandSizingMission")[0].to(ureg.kW).magnitude#hover
	P_battery[2] = sol("P_{battery}_OnDemandSizingMission")[4].to(ureg.kW).magnitude#reserve
	
	for j,offset in enumerate(offset_array):
		if (i == 0):
			if (j == 0):
				label = "Cruise"
			elif (j == 1):
				label = "Hover"
			elif (j == 2):
				label = "Reserve"

			plt.bar(i+offset,P_battery[j],align='center',alpha=1,width=width,color=colors[j],
				label=label)
		else:
			plt.bar(i+offset,P_battery[j],align='center',alpha=1,width=width,color=colors[j])

plt.grid()
plt.xticks(y_pos, labels, rotation=-45, fontsize=12)
plt.ylabel('Power (kW)', fontsize = 16)
plt.title("Power Consumption",fontsize = 18)
plt.legend(loc='upper right', fontsize = 12)

#Rotor tip Mach number 
plt.subplot(2,2,3)
for i, config in enumerate(configs):
	sol = configs[config]["solution"]
	MT = sol("MT_OnDemandSizingMission")[0]
	plt.bar(i,MT,align='center',alpha=1,color='k')

plt.grid()
plt.ylim(ymin=0.2)
plt.xticks(y_pos, labels, rotation=-45, fontsize=12)
plt.ylabel('Tip Mach number', fontsize = 16)
plt.title("Rotor Tip Mach Number",fontsize = 18)

#Rotor figure of merit 
plt.subplot(2,2,4)
for i, config in enumerate(configs):
	sol = configs[config]["solution"]
	FOM = sol("FOM_OnDemandSizingMission")[0]
	plt.bar(i,FOM,align='center',alpha=1,color='k')
plt.grid()
plt.ylim(ymin=0.7)
plt.xticks(y_pos, labels, rotation=-45, fontsize=12)
plt.ylabel('FOM (dimensionless)', fontsize = 16)
plt.title("Rotor Figure of Merit",fontsize = 18)

plt.suptitle(title_str,fontsize = 13.5)
plt.tight_layout()
plt.subplots_adjust(left=0.07,right=0.98,bottom=0.10,top=0.87)
plt.savefig('config_tradeStudy_plot_02.pdf')


#Cost breakdown plot
fig3 = plt.figure(figsize=(12,12), dpi=80)
plt.show()

#Revenue and deadhead costs

plt.subplot(3,2,1)
for i, config in enumerate(configs):
	
	cpsm = configs[config]["solution"]("cost_per_seat_mile_OnDemandMissionCost").to(ureg.mile**-1).magnitude
	
	p1 = plt.bar(i,cpsm,bottom=0,align='center',alpha=1,color="k")

plt.xticks(y_pos, labels, rotation=-45,fontsize=12)
plt.ylabel('Cost per seat mile ($US/mile)', fontsize = 14)
plt.grid()
plt.title("Cost per Seat Mile",fontsize = 16)

plt.subplot(3,2,2)
for i, config in enumerate(configs):
	
	c_vehicle = configs[config]["solution"]("purchase_price_OnDemandAircraft")/1e6
	c_avionics = configs[config]["solution"]("purchase_price_OnDemandAircraft/Avionics")/1e6
	c_battery = configs[config]["solution"]("purchase_price_OnDemandAircraft/Battery")/1e6
	
	p1 = plt.bar(i,c_vehicle,bottom=0,align='center',alpha=1,color="k")
	p2 = plt.bar(i,c_avionics,bottom=c_vehicle,align='center',alpha=1,color="lightgrey")
	p3 = plt.bar(i,c_battery,bottom=c_avionics+c_vehicle, align='center',alpha=1,color="w")

plt.xticks(y_pos, labels, rotation=-45,fontsize=12)
plt.ylabel('Cost ($millions US)', fontsize = 14)
plt.grid()
plt.ylim(ymax=1.7)
plt.title("Acquisition Costs",fontsize = 16)
plt.legend((p1[0],p2[0],p3[0]),("Vehicle","Avionics","Battery"),
	loc='upper right', fontsize = 12)

plt.subplot(3,2,3)
for i, config in enumerate(configs):
	
	c_revenue = configs[config]["solution"]("revenue_cost_per_trip_OnDemandMissionCost")
	c_deadhead = configs[config]["solution"]("deadhead_cost_per_trip_OnDemandMissionCost")
	
	p1 = plt.bar(i,c_revenue,bottom=0,align='center',alpha=1,color="k")
	p2 = plt.bar(i,c_deadhead,bottom=c_revenue,align='center',alpha=1,color="lightgrey")

plt.xticks(y_pos, labels, rotation=-45,fontsize=12)
plt.ylabel('Cost per trip ($US)', fontsize = 14)
plt.grid()
plt.ylim(ymax=300)
plt.title("Revenue and Deadhead Costs",fontsize = 16)
plt.legend((p1[0],p2[0]),("Revenue cost","Deadhead cost"),
	loc='upper right', fontsize = 12)

plt.subplot(3,2,4)
for i, config in enumerate(configs):
	
	c_capital = configs[config]["solution"]("cost_per_mission_OnDemandMissionCost/RevenueMissionCost/CapitalExpenses")
	c_operating = configs[config]["solution"]("cost_per_mission_OnDemandMissionCost/RevenueMissionCost/OperatingExpenses")
	
	p1 = plt.bar(i,c_capital,bottom=0,align='center',alpha=1,color="k")
	p2 = plt.bar(i,c_operating,bottom=c_capital,align='center',alpha=1,color="lightgrey")

plt.xticks(y_pos, labels, rotation=-45,fontsize=12)
plt.ylabel('Cost per mission ($US)', fontsize = 14)
plt.grid()
plt.ylim(ymax=250)
plt.title("Cost breakdown (revenue mission)",fontsize = 16)
plt.legend((p1[0],p2[0]),("Capital expenses (amortized)","Operating expenses"),
	loc='upper right', fontsize = 12)

plt.subplot(3,2,5)
for i, config in enumerate(configs):
	
	c_vehicle = configs[config]["solution"]("cost_per_mission_OnDemandMissionCost/RevenueMissionCost/CapitalExpenses/VehicleAcquisitionCost")
	c_avionics = configs[config]["solution"]("cost_per_mission_OnDemandMissionCost/RevenueMissionCost/CapitalExpenses/AvionicsAcquisitionCost")
	c_battery = configs[config]["solution"]("cost_per_mission_OnDemandMissionCost/RevenueMissionCost/CapitalExpenses/BatteryAcquisitionCost")
	
	p1 = plt.bar(i,c_vehicle,bottom=0,align='center',alpha=1,color="k")
	p2 = plt.bar(i,c_avionics,bottom=c_vehicle,align='center',alpha=1,color="lightgrey")
	p3 = plt.bar(i,c_battery,bottom=c_avionics+c_vehicle, align='center',alpha=1,color="w")

plt.xticks(y_pos, labels, rotation=-45,fontsize=12)
plt.ylabel('Cost per mission ($US)', fontsize = 14)
plt.grid()
plt.ylim(ymax=120)
plt.title("Capital Expenses (revenue mission)",fontsize = 16)
plt.legend((p1[0],p2[0],p3[0]),("Vehicle","Avionics","Battery"),
	loc='upper right', fontsize = 12)

plt.subplot(3,2,6)
for i, config in enumerate(configs):
	
	c_pilot = configs[config]["solution"]("cost_per_mission_OnDemandMissionCost/RevenueMissionCost/OperatingExpenses/PilotCost")
	c_maintenance = configs[config]["solution"]("cost_per_mission_OnDemandMissionCost/RevenueMissionCost/OperatingExpenses/MaintenanceCost")
	c_energy = configs[config]["solution"]("cost_per_mission_OnDemandMissionCost/RevenueMissionCost/OperatingExpenses/EnergyCost")
	IOC = configs[config]["solution"]("IOC_OnDemandMissionCost/RevenueMissionCost/OperatingExpenses")
	
	p1 = plt.bar(i,c_pilot,bottom=0,align='center',alpha=1,color="k")
	p2 = plt.bar(i,c_maintenance,bottom=c_pilot,align='center',alpha=1,color="lightgrey")
	p3 = plt.bar(i,c_energy,bottom=c_maintenance+c_pilot, align='center',alpha=1,color="w")
	p4 = plt.bar(i,IOC,bottom=c_energy+c_maintenance+c_pilot,align='center',alpha=1,color="grey")

plt.xticks(y_pos, labels, rotation=-45,fontsize=12)
plt.ylabel('Cost per mission ($US)', fontsize = 14)
plt.grid()
plt.ylim(ymax=160)
plt.title("Operating Expenses (revenue mission)",fontsize = 16)
plt.legend((p1[0],p2[0],p3[0],p4[0]),("Pilot","Maintanance","Energy","IOC"),
	loc='upper right', fontsize = 12)

cost_title_str = "Aircraft parameters: aircraft cost ratio = \$%0.0f per lb; battery cost ratio = \$%0.0f per kWh; %s\n" \
	% (vehicle_cost_per_weight.to(ureg.lbf**-1).magnitude, \
		battery_cost_per_C.to(ureg.kWh**-1).magnitude, autonomy_string) \
	+ "Pilot wrap rate = \$%0.0f/hour; mechanic wrap rate = \$%0.0f/hour; MMH per FH = %0.1f; deadhead ratio = %0.1f" \
	% (pilot_wrap_rate.to(ureg.hr**-1).magnitude, mechanic_wrap_rate.to(ureg.hr**-1).magnitude, \
		MMH_FH, deadhead_ratio)

plt.suptitle(cost_title_str,fontsize = 14)
plt.tight_layout()
plt.subplots_adjust(left=0.06,right=0.99,bottom=0.10,top=0.91)
plt.savefig('config_tradeStudy_plot_03_costBreakdown.pdf')


#Rotor data output (to text file)

output_data = open("rotor_data.txt","w")

output_data.write("Rotor design data (from sizing mission) \n\n")

output_data.write("Note: T and P are per rotor; SPL is for the entire vehicle.\n\n")

output_data.write("Configuration \tN \tR (m)\tT (N)\tP (W)\t")
output_data.write("VT (m/s)\tomega (rpm)\tMT\tFOM\tSPL (dB)\n")

for config in configs:
	 
	 sol = configs[config]["solution"]
	 
	 output_data.write(config)
	 output_data.write("\t%0.0f" % sol("N_OnDemandAircraft/Rotors"))
	 output_data.write("\t%0.3f" % sol("R_OnDemandAircraft/Rotors").to(ureg.m).magnitude)
	 output_data.write("\t%0.3e" % sol("T_perRotor_OnDemandSizingMission")[0].to(ureg.N).magnitude)
	 output_data.write("\t%0.3e" % sol("P_perRotor_OnDemandSizingMission")[0].to(ureg.W).magnitude)
	 output_data.write("\t%0.1f" % sol("VT_OnDemandSizingMission")[0].to(ureg.m/ureg.s).magnitude)
	 output_data.write("\t%0.0f" % sol("\omega_OnDemandSizingMission")[0].to(ureg.rpm).magnitude)
	 output_data.write("\t%0.3f" % sol("MT_OnDemandSizingMission")[0])
	 output_data.write("\t%0.3f" % sol("FOM_OnDemandSizingMission")[0])
	 SPL = 20*np.log10(sol("p_{ratio}_OnDemandSizingMission")[0])
	 output_data.write("\t%0.1f" % SPL)

	 output_data.write("\n")

output_data.close()
'''