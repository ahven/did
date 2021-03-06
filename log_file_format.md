# Job log file format

"Did" records all information in a job log file. Here's a description of the
format of that file.

The job log file is a text file with one event per line.

## Session start

A line that starts the session (a day) provides the session start time with second
resolution, and the word "arrive" meaning that you just arrived to work:

```
YYYY-MM-DD HH:MM:SS: arrive
```

The date must be in ISO format, followed by a space, and by time in 24-hour ISO
format.

In certain circumstances it might happen that you're working extra during a day
that shouldn't be treated as a working day. In that case use "arrive ooo"
(out-of-office).

```
YYYY-MM-DD HH:MM:SS: arrive ooo
```

Examples:

```
2019-12-17 09:05:23: arrive
```

```
2020-01-01 20:05:23: arrive ooo
```


## Tasks

A line indicating a task just provides a timestamp of when the task was completed
and the name of the task. The start time of the task is inferred from the end
time of the preceding line.

```
YYYY-MM-DD HH:MM:SS: task name
```

There are two kinds of tasks: work tasks and break tasks.
The type of a task is determined from the task's name.
Break tasks have names starting with the dot character (`.`), e.g. `.lunch`.
For compatibility with GTimeLog it's also accepted to have two consecutive
asterisks identified as a break, e.g. `lunch **`

All the events in the file must be ordered chronologically.
Otherwise an error is thrown.

## Complete day example

```
2019-12-17 09:05:23: arrive
2019-12-17 09:17:51: emails
2019-12-17 10:16:09: coding project-foo
2019-12-17 10:29:27: .coffee
2019-12-17 10:41:16: stand-up
2019-12-17 12:03:42: coding project-foo
2019-12-17 12:52:18: .lunch
2019-12-17 14:07:33: coding project-foo
2019-12-17 15:47:41: testing project-foo
2019-12-17 15:58:11: .tea
2019-12-17 16:32:37: team meeting
2019-12-17 17:37:02: coding project-foo
```

## Configuration

### Length of the working day

Must be set right before a session starts (i.e. preceding an "arrive"). Examples:
```
config daily_work_time = 8h
config daily_work_time = 6h
config daily_work_time = 3h20m
```

This can be set multiple times in the log file. Each settings is valid for all 
the sessions until a next setting comes.

### Daily breaks

Must be set right before a session starts (i.e. not in the middle of a session). Examples:
```
config paid_break "lunch" 15m daily splittable min_day_work_time=6h
config paid_break "screentime" 5m earn_work_time=1h splittable
config paid_break "screentime" 5m earn_work_time=1h one_chunk
config paid_break "lunch" delete
config paid_break "screentime" delete
```

Multiple breaks can be set at the same time. Each break has a unique name.
It's possible to modify a break by reusing the same name.
It's also possible to delete a break, so that it won't exist any more.
All the break tasks (tasks with)
