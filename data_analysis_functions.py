
# general packages
import os
import pandas as pd

# packages for dealing with dates
from datetime import timedelta, datetime

# packages for plotting
import matplotlib.pyplot as plt
import matplotlib



# ====================================
# |       READING IN THE DATA        |
# ====================================

def fix_colname(s):
    replace = {" ": "_",
               "(": "",
               ")": "",
              }

    new_s = s.lower()

    for k,v in replace.items():
        new_s = new_s.replace(k, v)

    return new_s


def read_in_data(data_folder_name):
    
    student_data_dict = {}
    all_student_data_df = pd.DataFrame()
    for data_file in os.listdir(os.path.join("Data", data_folder_name)):

        # define a student number from the data
        student_num = int(data_file[1])

        # read in the data
        if data_file.endswith('.csv'):
            student_data = pd.read_csv(os.path.join("Data", data_folder_name, data_file), encoding='windows-1252')
        elif data_file.endswith('.json'):
            student_data = pd.read_json(os.path.join("Data", ata_folder_name, data_file))
        
        # fix the column names
        student_data.columns = [fix_colname(c) for c in student_data.columns]
        
        # make the date column a timestamp
        student_data["date"] = pd.to_datetime(student_data["date"])
        
        # make the date column the index
        student_data.set_index("date", inplace=True)
        
        # turn the other coluns to datatimes
        if data_folder_name == 'sleepcycle_data':
            student_data["sleep_start"] = pd.to_datetime(student_data["sleep_start"])
            student_data["sleep_end"] = pd.to_datetime(student_data["sleep_end"])
        elif data_folder_name == 'loop_data':
            student_data["loop_time"] = pd.to_timedelta(student_data["loop_time"]+':00')
            
        # add an identifier for each student
        student_data["student_num"] = student_num
        
        # add this data to a map of the student number to the data
        student_data_dict[student_num] = student_data
        
        # add this data to a dataframe containing all students data
        all_student_data_df = pd.concat([all_student_data_df, student_data], axis=0)
        
    return all_student_data_df, student_data_dict


def clean_fitbit_data_df(original_fitbit_data_df):

    # clean the data and turn the values to floats
    all_fitbit_data_df = pd.DataFrame()
    for col in original_fitbit_data_df.columns:
        all_fitbit_data_df[col] = original_fitbit_data_df[col].replace(to_replace=",", value="", regex=True).astype(float)
        
    all_fitbit_data_df.index = original_fitbit_data_df.index.date

    return all_fitbit_data_df
    

def iter_over_dict_of_dfs(data_dict):

    for student, data in data_dict.items():
        print("------------------------------------------------------------")
        print("Student", student)
        print(data)


def read_and_clean_foodbook_data():
    
    # read in foodbook data
    full_foodbook_data = pd.read_csv(os.path.join('Data', 'foodbook_data', 'student_food_data.csv'))
    
    # fix the column names
    full_foodbook_data.columns = [fix_colname(c) for c in full_foodbook_data.columns]
    
    # add a student number column
    full_foodbook_data['student_num'] = full_foodbook_data.apply(lambda row: int(row["email"][1]), axis=1)

    # turn the date to timstamp
    full_foodbook_data['date'] = pd.to_datetime(full_foodbook_data['date'])

    # set the date column as the index
    full_foodbook_data.set_index("date", inplace=True)

    # iterate through and seperate each students data
    foodbook_data_dict = {}
    for stud_num in full_foodbook_data["student_num"].unique():
        student_df = full_foodbook_data[full_foodbook_data["student_num"] == stud_num]
        foodbook_data_dict[stud_num] = student_df.drop(columns=["email"])
        
    return full_foodbook_data.drop(columns=["email"]), foodbook_data_dict


def add_studs_to_list(data_dict, stud_list):

    for student_num in data_dict.keys():
        if student_num not in stud_list:
            stud_list.append(student_num)



# ====================================
# |          SLEEP ANALYSIS          |
# ====================================

def round_time(dt, round_to=60):

    """
    Round a datetime object to any time lapse in seconds

    Params:
       dt: datetime.datetime object or timedelta object
       round_to: Closest number of seconds to round to, default 1 minute
    """
    
    try:
        # treat it as a timedelta object
        rounding = ((dt.seconds + (round_to/2)) // round_to) * round_to

        return dt + timedelta(0, rounding - dt.seconds)

    except:
        # treat it as a datetime object
        rounding = ((dt.second + (round_to/2)) // round_to) * round_to

        return dt + timedelta(0, rounding - dt.second)


def time_to_seconds(row, col_name, alter_by_1_day):
    
    time = row[col_name].time()
    
    time_in_seconds = (time.hour * 60 + time.minute) * 60 + time.second
    
    if alter_by_1_day:
        if time_in_seconds < 50000: # before 1:53pm
            #print(round_time(datetime.fromtimestamp(50000), round_to=60))
            #print(round_time(datetime.fromtimestamp(time_in_seconds), round_to=60), "-->", round_time(datetime.fromtimestamp(time_in_seconds + (24 * 60 * 60)), round_to=60))
            time_in_seconds += (24 * 60 * 60)
            
    return time_in_seconds


def convert_secs_to_hours(seconds, remainder):

    if remainder:
        # get the number of hours
        hours = seconds / 3600
        return round(hours, 2)
    else:
        hours = seconds // 3600
        return "%dhrs" % (hours)


def convert_secs_to_time(seconds):
    
    timestamp = datetime.fromtimestamp(int(seconds))
    rounded = round_time(timestamp, round_to=60)
    str_time = str(rounded)[-8:-6].lstrip("0")
    
    if timestamp.day == 1:
        if int(str_time) > 12:
            return str(int(str_time) - 12) + "pm"
        elif int(str_time) == 12:
            return str_time + "pm"
        
        else:
            return str_time + "am"
    elif timestamp.day == 2:
        if str_time == "":
            return "12am"
        else:
            return str_time + "am"


def update_global_val(max_or_min, series_of_vals, global_val):
    
    if max_or_min == "min":
        min_time = min(series_of_vals)
        if min_time < global_val:
            return min_time
        else:
            return global_val

    elif max_or_min == "max":
        max_time = max(series_of_vals)
        if global_val < max_time:
            return max_time
        else:
            return global_val


def plot_raw_sleep_data(sleepcycle_data_dict, stud_list):

    fig = plt.figure(figsize=(40,16))
    gs = fig.add_gridspec(ncols=1, nrows=len(stud_list), wspace=0, hspace=0)
    axes = gs.subplots(sharex='col', sharey=False)

    # set the axes column names
    axes[0].set_title('Sleep Schedule Over Time', size=40)

    # set the axes row names
    for ax, stud_num in zip(axes, stud_list):
        ax.set_ylabel("Student_"+str(stud_num), size=20, rotation='horizontal', labelpad=55)

    # plot the sleep schedule for each person
    global_min = pd.Timestamp(2200, 12, 31)
    global_max = pd.Timestamp(2000, 1, 1)
    for stud_num in stud_list:

        # get the data for that sudent
        if stud_num in sleepcycle_data_dict:

            sleepcycle_df = sleepcycle_data_dict[stud_num]

            # get the minimum and maximum dates for that sudent
            global_min = update_global_val("min", sleepcycle_df["sleep_start"], global_min)
            global_max = update_global_val("max", sleepcycle_df["sleep_start"], global_max)

            # plot the sleep periods for this student
            axes[stud_num-1].eventplot(sleepcycle_df["sleep_start"], orientation='horizontal', color="blue", linelengths=0.4)
            axes[stud_num-1].eventplot(sleepcycle_df["sleep_end"], orientation='horizontal', color="red", linelengths=0.4)
            for index, row in sleepcycle_df.iterrows():
                axes[stud_num-1].hlines(1, row["sleep_start"], row["sleep_end"])

            # add text of how long the sleep was
            for index, row in sleepcycle_df.iterrows():
                time_in_bed = str(round_time(row["sleep_end"] - row["sleep_start"], round_to=60))[-8:-3]
                midpoint_of_sleep = row["sleep_start"] + (row["sleep_end"] - row["sleep_start"])//2
                axes[stud_num-1].annotate(text=time_in_bed, xy=(midpoint_of_sleep, 1.25), ha='center', fontsize=14)

        # remove the y-tick labels
        axes[stud_num-1].tick_params(axis='y', which='both', labelleft=False)

        # add gridlines to show each day on the x-axis
        axes[stud_num-1].grid(axis='x')

    # make sure the x-axis has all days
    date_range = pd.date_range(start=global_min, end=global_max)
    axes[0].set_xticks(date_range)

    # set the fontsize of the x-axis labels & rotate these labels
    _ = plt.xticks(fontsize=18, rotation=90)


def plot_aggregated_sleep_schedules(sleepcycle_data_dict, stud_list, gridlines):

    fig = plt.figure(figsize=(35,16))
    gs = fig.add_gridspec(ncols=3, nrows=len(stud_list), wspace=0.1, hspace=0)
    axes = gs.subplots(sharex='col', sharey=True)

    # set the axes column names
    axes[0, 0].set_title('Bed time', size=30)
    axes[0, 1].set_title('Wake up time', size=30)
    axes[0, 2].set_title('Time in bed', size=30)

    # set the axes row names
    for ax, stud_num in zip(axes[:, 0], stud_list):
        ax.set_ylabel("Student_"+str(stud_num), size=20, rotation='horizontal', labelpad=55)

    # set up the formatter for changing seconds to time
    from_seconds_formatter = matplotlib.ticker.FuncFormatter(lambda s, x: convert_secs_to_time(s))
    from_timedelta_formatter = matplotlib.ticker.FuncFormatter(lambda s, x: convert_secs_to_hours(s, remainder=False))

    # plot a boxplot of the average sleep schedule for each person
    global_min_start = global_min_end = global_min_in_bed = 10000000
    global_max_start = global_max_end = global_max_in_bed = 0
    for stud_num in stud_list:
        
        # get the data for that sudent
        if stud_num in sleepcycle_data_dict:
                
            sleepcycle_df = sleepcycle_data_dict[stud_num].copy()
            
            # plot the average time this student goes to bed
            sleepcycle_df["time_start"] = sleepcycle_df.apply(lambda row: time_to_seconds(row, "sleep_start", alter_by_1_day=True), axis=1)
            global_min_start = update_global_val("min", sleepcycle_df["time_start"], global_min_start)
            global_max_start = update_global_val("max", sleepcycle_df["time_start"], global_max_start)
            axes[stud_num-1, 0].boxplot(sleepcycle_df["time_start"], vert=False)

            # plot the average time this student wakes up
            sleepcycle_df["time_end"] = sleepcycle_df.apply(lambda row: time_to_seconds(row, "sleep_end", alter_by_1_day=False), axis=1)
            global_min_end = update_global_val("min", sleepcycle_df["time_end"], global_min_end)
            global_max_end = update_global_val("max", sleepcycle_df["time_end"], global_max_end)
            axes[stud_num-1, 1].boxplot(sleepcycle_df["time_end"], vert=False)

            # plot the average time this student spends to bed
            sleepcycle_df["time_in_bed"] = sleepcycle_df.apply(lambda row: round_time(row["sleep_end"]-row["sleep_start"], round_to=60).total_seconds(), axis=1)
            global_min_in_bed = update_global_val("min", sleepcycle_df["time_in_bed"], global_min_in_bed)
            global_max_in_bed = update_global_val("max", sleepcycle_df["time_in_bed"], global_max_in_bed)
            axes[stud_num-1, 2].boxplot(sleepcycle_df["time_in_bed"].astype(int), vert=False)

        
        # remove the y-tick labels
        axes[stud_num-1, 0].tick_params(axis='y', which='both', labelleft=False)
        
        # change the x-axis to an hourly interval (2hr for wake up time)
        one_hr = 3600
        axes[stud_num-1, 0].set_xticks([unix_time for unix_time in range(global_min_start, global_max_start+1) if unix_time % one_hr == 0])
        axes[stud_num-1, 1].set_xticks([unix_time for unix_time in range(global_min_end, global_max_end+1) if unix_time % (2 * one_hr) == 0])
        axes[stud_num-1, 2].set_xticks([unix_time for unix_time in range(int(global_min_in_bed), int(global_max_in_bed)+1) if unix_time % one_hr == 0])
        
        # format the x-axis to be a date
        axes[stud_num-1, 0].xaxis.set_major_formatter(from_seconds_formatter)
        axes[stud_num-1, 1].xaxis.set_major_formatter(from_seconds_formatter)
        axes[stud_num-1, 2].xaxis.set_major_formatter(from_timedelta_formatter)
        
        if gridlines:
            # add gridlines to show each day on the x-axis
            axes[stud_num-1, 0].grid(axis='x')
            axes[stud_num-1, 1].grid(axis='x')
            axes[stud_num-1, 2].grid(axis='x')

        # set the fontsize of the x-axis labels & rotate these labels
        plt.sca(axes[stud_num-1, 0])
        plt.xticks(fontsize=15)
        plt.sca(axes[stud_num-1, 1])
        plt.xticks(fontsize=15)
        plt.sca(axes[stud_num-1, 2])
        plt.xticks(fontsize=15)



# ====================================
# |          LOOP ANALYSIS           |
# ====================================

def plot_num_ips(all_loop_data_df):

    ax = all_loop_data_df[["student_num", "ip_address"]].groupby('student_num').nunique().reset_index().plot.bar(x='student_num', y='ip_address', title="The number IP addresses each student has had")
    ax.legend(["IP addresses"])
    ax.set_xlabel("Student ID")
    ax.set_ylabel("# IP addresses")
    ax.get_legend().remove()


def plot_num_activities_on_loop(count_activities_df):

    ax = count_activities_df.plot.bar(x='student_num', y='loop_time', title="The number of interactions each student has with loop")
    ax.legend(["Activity"])
    ax.set_xlabel("Student ID")
    ax.set_ylabel("Activity on loop")
    ax.get_legend().remove()


def calculate_students_time_on_loop(all_loop_data_df):

    stud_nums = set(all_loop_data_df["student_num"])
    time_spent_df = pd.DataFrame(columns=["student_num", "total_hours"], index=list(range(len(stud_nums))))
    for i, stud_num in enumerate(stud_nums):
        students_data = all_loop_data_df[all_loop_data_df["student_num"] == stud_num]

        total_time = 0
        prev_time = students_data.iloc[0, :]["loop_time"]
        for time in students_data.iloc[1:, :]["loop_time"]:

            # see how long was between these times
            time_between = time - prev_time

            # if there was less than 5 minutes (300 secs) between these events, we assume the person was active for this full time
            if time_between.total_seconds() > 300:
                total_time += time_between.total_seconds()
        
        time_spent_df.loc[i, "student_num"] = stud_num
        time_spent_df.loc[i, "total_hours"] = convert_secs_to_hours(total_time, True)

    return time_spent_df


def plot_length_of_time_on_loop(time_spent_df):

    ax = time_spent_df.plot.bar(x='student_num', y='total_hours', title="The total time each student spent on loop")
    ax.legend(["Time"])
    ax.set_xlabel("Student ID")
    ax.set_ylabel("Time Spent on loop (hrs)")
    ax.get_legend().remove()


def plot_time_and_num_activities_on_loop(time_spent_df, count_activities_df):

    fig, ax_left = plt.subplots(figsize=(16, 16))
    ax_right = ax_left.twinx()

    # label the plot
    ax_left.set_xlabel("Student ID", fontsize=20)
    ax_left.set_title("Time spent & number of interactions each student had with loop\n", fontsize=30)

    # plot the number of activities done on loop
    ax_left.bar(time_spent_df["student_num"]-0.21, time_spent_df["total_hours"], width=0.4, color="blue")
    ax_left.set_ylabel("Total Hours spent on Loop", fontsize=20)
    ax_left.yaxis.label.set_color("blue")

    # plot the time spent on loop
    ax_right.bar(count_activities_df["student_num"]+0.21, count_activities_df["loop_time"], width=0.4, color="red")
    ax_right.set_ylabel("# Interactions with Loop", fontsize=20)
    ax_right.yaxis.label.set_color("red")


def plot_time_distribution(all_loop_data_df):

    fig = plt.figure(figsize=(20,20))
    plt.title("Distribution of loop interactions throughout the day", fontsize=30)

    # get the distribution of times in this dataset
    fixed_time_df = pd.DataFrame([val.time() for val in pd.to_datetime(all_loop_data_df["loop_time"].astype(str).str[-8:])]).rename(columns={0:"loop_time"})
    fixed_time_df["count"] = fixed_time_df["loop_time"]
    count_df = fixed_time_df.groupby("loop_time").count().reset_index()

    plt.bar(list(count_df["loop_time"].astype(str)), height=list(count_df["count"]))
    plt.ylabel("Num Interactions", fontsize=20)
    #plt.xticks(list(count_df["loop_time"].astype(str)), fontsize=20, rotation=90)


# ====================================
# |         FITBIT ANALYSIS          |
# ====================================

def plot_time_at_each_activity_level(all_fitbit_data_df, stud_list):

    fig = plt.figure(figsize=(20,20))
    gs = fig.add_gridspec(ncols=1, nrows=len(stud_list), wspace=0, hspace=0)
    ax_left = gs.subplots(sharex='col', sharey=False)

    # set the axes column name
    ax_left[0].set_title('Breakdown of activity levels', size=30)

    # set the axes row names
    for ax, stud_num in zip(ax_left, stud_list):
        ax.set_ylabel("Student_"+str(stud_num), size=20, rotation='horizontal', labelpad=55)

    relevant_cols = [#"minutes_sedentary",
                     "minutes_lightly_active", "minutes_fairly_active", "minutes_very_active"]
    for stud_num in stud_list:

        student_df = all_fitbit_data_df[all_fitbit_data_df["student_num"] == stud_num]

        # plot the bar plots
        activity_levels_df = student_df[relevant_cols]
        plot_1 = activity_levels_df.plot.bar(ax=ax_left[stud_num-1], stacked=True, legend=False)

        # Shorten the activity y-axes limits
        ax_left[stud_num-1].set_ylim([0, 380])

        # plot the calories burned on this axis
        #calories_df = student_df["calories_burned"]
        #calories_df.plot.line(ax=ax_left[stud_num-1], secondary_y=True)


    # set the fontsize of the x-axis labels & rotate these labels
    plt.sca(ax_left[stud_num-1])
    plt.xticks(fontsize=15)

    # define one legend at the very top of the plot
    handles, labels = ax_left[stud_num-1].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', fontsize=20, ncol=len(relevant_cols))
    plt.show()


# ====================================
# |        FOODBOOK ANALYSIS         |
# ====================================

def plot_calorie_intake_vs_output(all_foodbook_data_df, all_fitbit_data_df, stud_list):

    fig = plt.figure(figsize=(20,20))
    gs = fig.add_gridspec(ncols=1, nrows=len(stud_list), wspace=0, hspace=0)
    axes = gs.subplots(sharex='col', sharey=True)

    # set the axes column name
    axes[0].set_title('Calorie Intake Vs Output', size=30)

    # set the axes row names
    for ax, stud_num in zip(axes, stud_list):
        ax.set_ylabel("Student_"+str(stud_num), size=20, rotation='horizontal', labelpad=55)

    # group the data by the student and the date & sum the calories
    grouped_foodbook_df = all_foodbook_data_df[["student_num", "energy_kcal"]].groupby(["date", "student_num"]).sum().reset_index().set_index("date")

    for stud_num in stud_list:

        food_student_df = grouped_foodbook_df[grouped_foodbook_df["student_num"] == stud_num]
        activity_student_df = all_fitbit_data_df[all_fitbit_data_df["student_num"] == stud_num]

        # plot the input calories
        food_calorie_df = food_student_df["energy_kcal"]
        food_calorie_df.plot.line(ax=axes[stud_num-1])

        # plot the expended calories
        activity_calories_df = activity_student_df["calories_burned"]
        activity_calories_df.plot.line(ax=axes[stud_num-1])

    # set the fontsize of the x-axis labels & rotate these labels
    plt.sca(axes[stud_num-1])
    plt.xticks(fontsize=15)
   
    # remove the label from the x-axis
    axes[stud_num-1].get_xaxis().get_label().set_visible(False)
    plt.show()


# ====================================
# |        ALL DATA ANALYSIS         |
# ====================================

def merge_the_data(all_sleep_data_df, all_loop_data_df, all_fitbit_data_df, all_foodbook_data_df):

    fit_sleep = all_fitbit_data_df.reset_index().join(all_sleep_data_df.reset_index(), on=["date", "student_num"], how='outer')
    fit_sleep_food = fit_sleep.join(all_foodbook_data_df.reset_index(), on=["date", "student_num"], how='outer')

    return fit_sleep_food


def plot_all_data(merged_df):

    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')

    # title the axes
    ax.set_xlabel('Time In Bed', fontsize=10)
    ax.set_ylabel('Activity Level', fontsize=10)
    ax.set_zlabel('Calories Consumed', fontsize=10)
    ax.set_title("Plotting people by their sleep, activity & food")

    # get the values
    merged_df["time_in_bed"] = merged_df.apply(lambda row: round_time(row["sleep_end"]-row["sleep_start"], round_to=60).total_seconds(), axis=1)

    ax.scatter(merged_df["time_in_bed"], )


def plot_3d_principal_component_points(targets, colours, column_to_colour_cluster_with):
    
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')

    # title the axes
    ax.set_xlabel('Time In Bed', fontsize=10)
    ax.set_ylabel('Activity Level', fontsize=10)
    ax.set_zlabel('Calories Consumed', fontsize=10)
    ax.set_title("Plotting people by their sleep, activity & food")

    # set limits on the plot
    #ax.set_xlim([-0.23, 0.4])
    #ax.set_ylim([-0.2, 0.3])
    #ax.set_zlim([-0.15, 0.3])

    # plot the points
    for target, colour in zip(targets, colours):
        ax.scatter(pc1.loc[column_to_colour_cluster_with == target], pc2.loc[column_to_colour_cluster_with == target], pc3.loc[column_to_colour_cluster_with == target], c=colour, s=100, marker='o', edgecolors='grey')
    
    if not pca_centroid_df.empty:
        ax.scatter(pca_centroid_df['PC1'], pca_centroid_df['PC2'], pca_centroid_df['PC3'], c='black', s=100, marker='X')
        
    ax.legend(targets)
    plt.show()
