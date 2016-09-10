#!/usr/bin/python

import sys, glob, os, argparse


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
    parser.add_argument('-d', '--directory', metavar='directory', default='', help='Directory to look for iCal files.')
    parser.add_argument('-b', '--buffer', metavar='buffer', type=int, default=5,
                        help='Buffer between events, in minutes.')
    parser.add_argument('-s', '--starttime', metavar='starttime', type=int, default=700,
                        help='Start of free time. 24H format')
    parser.add_argument('-e', '--endtime', metavar='endtime', type=int, default=2400,
                        help='End of free time. 24H format')
    parser.add_argument('-m', '--mintime', metavar='mintime', type=int, default=30,
                        help='Min amount of free time between events')
    # parser.print_help()
    args = parser.parse_args()
    os.chdir(args.directory)
    times = {'free': Cal()}
    for file in glob.glob('*.ics'):
        times[file.title()] = Cal()
        parse_cal(file, times)

    for day in range(5):  # 5 times for each day of the week
        day_list = combine_day(day, times)
        while len(day_list) > 1:
            free_time = earliest_free(day_list)
            if free_time is not None:
                times['free'].add_time(free_time, day)
            day_list = day_list[1:]
    print('done')


def combine_day(day, times):
    day_list = []
    for key, cur_cal in times.items():
        if len(cur_cal.days[day]) > 0:
            for cur_time in cur_cal.days[day]:
                day_list.append(cur_time)
                day_list.sort()
    return day_list


def earliest_free(day_list):
    start = day_list[0]
    for index, cur in enumerate(day_list[1:]):
        if start[1] < cur[0]:
            return start[1], cur[0]
        else:
            start = cur
    return None


def parse_cal(file, times):
    """extracts the start/end times from a given calendar file
    and stores each calendars' info in a dictionary by file name"""
    found = False
    with open(file, 'r') as f:
        for line in f:
            if found:
                start_time = line[line.find('T', line.find('York') + 4) + 1:len(line) - 1]
                line = next(f)
                end_time = line[line.find('T', line.find('York') + 4) + 1:len(line) - 1]
                line = next(f)
                cur_day = line[line.find('BYDAY') + 6:len(line) - 1]
                time_range = (int(start_time), int(end_time))
                times.get(file.title()).add_time(time_range, cur_day)
                found = False
            if 'BEGIN:VEVENT' in line:
                found = True


if __name__ == '__main__':
    main()
