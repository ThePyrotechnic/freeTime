#!/usr/bin/python

import argparse
import glob
import os
from datetime import timedelta


class Cal:
    def __init__(self):
        self.mon = []
        self.tues = []
        self.wed = []
        self.thurs = []
        self.fri = []
        self.days = (self.mon, self.tues, self.wed, self.thurs, self.fri)

    def add_time(self, time, day):
        if day == 'MO' or day == 0:
            self.mon.append(time)
            self.mon.sort()
        elif day == "TU" or day == 1:
            self.tues.append(time)
            self.tues.sort()
        elif day == "WE" or day == 2:
            self.wed.append(time)
            self.wed.sort()
        elif day == "TH" or day == 3:
            self.thurs.append(time)
            self.thurs.sort()
        elif day == "FR" or day == 4:
            self.fri.append(time)
            self.fri.sort()


def main():

    parser = argparse.ArgumentParser(
        description='Takes iCal files, finds a weekly schedule, and returns the free time shared between all files.',
        prog='freeTime',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d', '--directory', metavar='directory', type=str, default=os.getcwd(), help='Directory to look for iCal files.')
    parser.add_argument('-b', '--buffer', metavar='buffer', type=int, default=5,
                        help='Buffer between events, in minutes.')
    parser.add_argument('-s', '--starttime', metavar='starttime', type=int, default=70000,
                        help='Start of free time. (HHMMSS)')
    parser.add_argument('-e', '--endtime', metavar='endtime', type=int, default=240000,
                        help='End of free time. (HHMMSS)')
    parser.add_argument('-m', '--mintime', metavar='mintime', type=int, default=30,
                        help='Min amount of free time between events')
    parser.add_argument('-n', '--filename', metavar='filename', type=str, default='freetime',
                        help='Name of output file (Omit file extension)')
    # parser.print_help()
    args = parser.parse_args()
    buffer = args.buffer
    min_time = args.mintime

    print(os.getcwd())
    os.chdir(args.directory)
    times = {'free': Cal()}

    ret = None
    for file in glob.glob('*.ics'):
        times[file.title()] = Cal()
        ret = parse_cal(file, times)
    if ret is not None:
        start_date = ret[0]
        end_date = ret[1]
        tzid = ret[2]
    else:
        print('No .ics files found in ' + '(' + args.directory + ')')
        return
    for day in range(5):  # 5 times for each day of the week
        day_list = combine_day(day, times)
        add_freetime_caps(day_list, day, args.starttime, args.endtime, buffer, min_time, times['free'])
        while len(day_list) > 1:
            free_time = parse_range(earliest_free(day_list), buffer, min_time)
            if free_time is not None:
                if free_time not in times['free'].fri:
                    times['free'].add_time(free_time, day)
            day_list = day_list[1:]

    free_cal = open(args.filename + '.ics', 'w')  # Create iCal file
    free_cal.write('BEGIN:VCALENDAR\n'
                   'PRODID:-//FREETIME\n'
                   'VERSION:2.0\n'
                   'CALSCALE:GREGORIAN\n'
                   'METHOD:PUBLISH\n'
                   'X-WR-CALNAME:Free Time\n'
                   'X-WR-TIMEZONE:America/New_York\n'
                   'X-WR-CALDESC:Free time between given schedules\n'
                   'BEGIN:VTIMEZONE\n'
                   'TZID:America/New_York\n'
                   'X-LIC-LOCATION:America/New_York\n'
                   'BEGIN:DAYLIGHT\n'
                   'TZOFFSETFROM:-0500\n'
                   'TZOFFSETTO:-0400\n'
                   'TZNAME:EDT\n'
                   'DTSTART:19700308T020000\n'
                   'RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU\n'
                   'END:DAYLIGHT\n'
                   'BEGIN:STANDARD\n'
                   'TZOFFSETFROM:-0400\n'
                   'TZOFFSETTO:-0500\n'
                   'TZNAME:EST\n'
                   'DTSTART:19701101T020000\n'
                   'RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU\n'
                   'END:STANDARD\n'
                   'END:VTIMEZONE\n\n')

    for index, cur_day in enumerate(times['free'].days):
        for time in cur_day:
            if time is not None:  # TODO simplify this
                if len(str(time[0])) < 6:
                    start_time = '0' + str(time[0])
                else:
                    start_time = str(time[0])

                if len(str(time[1])) < 6:
                    end_time = '0' + str(time[1])
                else:
                    end_time = str(time[1])

                free_cal.write('BEGIN:VEVENT\n'
                               'DTSTART;TZID=' + tzid + ':' + start_date + 'T' + start_time + '\n' +
                               'DTEND;TZID=' + tzid + ':' + start_date + 'T' + end_time + '\n' +
                               'RRULE:FREQ=WEEKLY;UNTIL=' + end_date + 'T000000Z;BYDAY=' + convert_day(index) + '\n' +
                               'SUMMARY:Free Time\n' +
                               'END:VEVENT' + '\n\n')
    free_cal.write('END:VCALENDAR')
    free_cal.close()
    print('Done. Free time calendar created at ' + args.directory + '\\' + args.filename + '.ics')


def combine_day(day, times):
    """
    combines time ranges for a certain day from multiple calendar objects into one list
    :param day: the day to work with (0-4)
    :param times: the list of calendars to pull from
    :return the unified list
    """
    day_list = []
    for key, cur_cal in times.items():
        if len(cur_cal.days[day]) > 0:
            for cur_time in cur_cal.days[day]:
                day_list.append(cur_time)
    day_list.sort()
    return day_list


def earliest_free(day_list):
    """
    finds the first range of free time given a list of busy ranges
    :param day_list: the list of busy ranges
    :return: the earliest free time if there is one, or null
    """
    start = day_list[0]
    for index, cur in enumerate(day_list[1:]):
        if start[1] < cur[0]:
            return start[1], cur[0]
        else:
            start = cur
    return None


def parse_cal(file, times):
    """
    extracts the start/end times from a given calendar file
    and stores each calendars' info in a dictionary by file name
    :param file: the calendar file
    :param times: the list of calendar objects
    :return: the extracted time zone, start date of this schedule, and end date, or none if already returned.
                right now the program assumes it is the same for each schedule given
    """
    start_date = None
    end_date = None
    tzid = None
    found = False

    with open(file, 'r') as f:
        for line in f:
            if found:
                start_time = line[line.find(':') + 10:len(line) - 1]
                if start_date is None:
                    start_date = line[line.find(':') + 1:len(line) - 8]
                    tzid = line[line.find('=') + 1:line.find(':')]
                line = next(f)

                end_time = line[line.find(':') + 10:len(line) - 1]
                line = next(f)

                cur_day = line[line.find('BYDAY') + 6:len(line) - 1]

                if end_date is None:
                    end_date = line[line.find('UNTIL=') + 6:len(line) - 18]
                time_range = (int(start_time), int(end_time))
                times.get(file.title()).add_time(time_range, cur_day)
                found = False

            if 'BEGIN:VEVENT' in line:
                found = True
    if start_date is not None:
        return [start_date, end_date, tzid]
    return None


def convert_day(num):
    """
    converts an integer 0 > num > 4 to a string day for formatting
    :param num: the num to convert
    :return: the string, or ERROR
    """
    days = ['MO', 'TU', 'WE', 'TH', 'FR']
    if num < 0 or num > 4:
        return 'ERROR'
    else:
        return days[num]


def parse_range(time_range, buffer, min_time):
    """
    checks if a time range meets the minimum req. and adds the buffer
    :param time_range: the range to parse
    :param buffer: how much time to pad the interval with
    :param min_time: the minimum length that the interval must be to be valid
    :return: the range if valid, null otherwise
    """
    if time_range is None:
        return None

    if len(str(time_range[0])) < 6:
        t1_val = '0' + str(time_range[0])
    else:
        t1_val = str(time_range[0])

    if len(str(time_range[1])) < 6:
        t2_val = '0' + str(time_range[1])
    else:
        t2_val = str(time_range[1])

    t1 = timedelta(seconds=int(t1_val[4:]), minutes=int(t1_val[2:4]) + buffer,
                   hours=int(t1_val[0:2]))
    t2 = timedelta(seconds=int(t2_val[4:]), minutes=int(t2_val[2:4]) - buffer,
                   hours=int(t2_val[0:2]))
    if (t2 - t1).seconds >= min_time * 60:  # TODO loop this?
        hours, remainder = divmod(t1.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if len(str(hours)) < 2:
            hours = '0' + str(hours)
        if len(str(minutes)) < 2:
            minutes = '0' + str(minutes)
        if len(str(seconds)) < 2:
            seconds = '0' + str(seconds)
        t1 = int('{}{}{}'.format(hours, minutes, seconds))

        hours, remainder = divmod(t2.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if len(str(hours)) < 2:
            hours = '0' + str(hours)
        if len(str(minutes)) < 2:
            minutes = '0' + str(minutes)
        if len(str(seconds)) < 2:
            seconds = '0' + str(seconds)
        t2 = int('{}{}{}'.format(hours, minutes, seconds))

        return t1, t2
    else:
        return None


def add_freetime_caps(day_list, day, starttime, endtime, buffer, min_time, free_cal):
    """
    Adds free time values for the beginning and end of each day (the "caps" on top and bottom)
    :param day_list: The list of free times for each day
    :param day: The day in question
    :param starttime: The minimum allowed start time
    :param endtime: The maximum allowed end time
    :param buffer: the buffer added on the start and end of all free times
    :param min_time: the minimum amount of time considered free
    :param free_cal: the calendar to add the resulting times to
    :return: None
    """
    if len(day_list) > 0:
        if starttime < day_list[0][0]:  # TODO use time objects
            free_cal.add_time(parse_range((starttime, day_list[0][0]), buffer, min_time), day)
        if endtime > day_list[-1][1]:
            free_cal.add_time(parse_range((day_list[-1][1], endtime), buffer, min_time), day)
    else:
        free_cal.add_time(parse_range((starttime, endtime), buffer, min_time), day)


if __name__ == '__main__':
    main()
