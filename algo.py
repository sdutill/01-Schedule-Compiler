class Schedule:
    def __init__(self):
        self.days = {
            'monday': [],
            'tuesday': [],
            'wednesday': [],
            'thursday': [],
            'friday': [],
        }

    def add_timeslot(self, day, start_time, end_time):
        if day not in self.days:
            print(f"Invalid day: {day}")
            return
        
        time_slot = (start_time, end_time)
        
        self.days[day].append(time_slot)
        
    def add_class(self, class_meetingTimes):
        for day, new_timeslots in class_meetingTimes.days.items():
            for new_timeslot in new_timeslots:
                for existing_timeslot in self.days[day]:
                    if self.timeslots_overlap(existing_timeslot, new_timeslot):
                        return False
                
        for day, new_timeslots in class_meetingTimes.days.items():
            for new_timeslot in new_timeslots:
                self.days[day].append(new_timeslot)
            
        return True

    def remove_class(self, class_meetingTimes):
        for day, timeslots in class_meetingTimes.days.items():
            for timeslot in timeslots:
                self.days[day].remove(timeslot)
                
    @staticmethod
    def timeslots_overlap(slot1, slot2):
        start1, end1 = slot1
        start2, end2 = slot2
        return not (end1 <= start2 or end2 <= start1)
    
    def copy(self):
        new_schedule = Schedule()
        for day, timeslots in self.days.items():
            for timeslot in timeslots:
                new_schedule.add_timeslot(day, timeslot[0], timeslot[1])
        return new_schedule
        
    def __str__(self):
        return str(self.days)

def dfs_build_rosters(course_info, course_keys, index, roster, valid_rosters):
    # If 5 schedules have already been created, return
    if len(valid_rosters) >= 5:
        return
    # If all courses have been considered, add the current roster to valid_rosters
    if index == len(course_keys):
        valid_rosters.append(roster.copy())
        return

    course_key = course_keys[index]
    for section in course_info[course_key]:
        if roster.add_class(section['schedule']):
            dfs_build_rosters(course_info, course_keys, index + 1, roster, valid_rosters)
            roster.remove_class(section['schedule'])

def build_all_valid_rosters(course_info, course_list):
    valid_rosters = []
    dfs_build_rosters(course_info, course_list, 0, Schedule(), valid_rosters)
    # Sort the times in each schedule before returning
    sorted_valid_rosters = []

    for roster in valid_rosters:
        sorted_roster = Schedule()
        for day, timeslots in roster.days.items():
            sorted_timeslots = sorted(timeslots)
            for timeslot in sorted_timeslots:
                sorted_roster.add_timeslot(day, timeslot[0], timeslot[1])
        sorted_valid_rosters.append(sorted_roster)

    return sorted_valid_rosters