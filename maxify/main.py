#!/usr/bin/env python

"""
Main module for maxify command line application.
"""

import argparse
import cmd
import shlex

import colorama
from maxify.units import ParsingError
from termcolor import colored

from maxify.config import import_config
from maxify.repo import Repository, Projects


class MaxifyCmd(cmd.Cmd):
    """Command interpreter used for accepting commands from the user to
    manage a Maxify project.

    """

    def __init__(self, stdin=None, stdout=None, use_color=True):
        cmd.Cmd.__init__(self, stdin=stdin, stdout=stdout)
        self.intro = "Maxify programmer time tracker client"
        self.prompt = "> "
        self.current_project = None
        self.use_color = use_color
        self.projects = Projects()

    def cmdloop(self, project_name=None):
        if project_name:
            self._set_current_project(project_name)
            if self.current_project:
                self.intro = self.intro + \
                    "\n\n" + \
                    "Switched to project '{0}'".format(
                        self.current_project.name)
            else:
                self.intro = self.intro + \
                    "\n\nNo project found named '{0}'".format(project_name)

        cmd.Cmd.cmdloop(self)

    def _set_current_project(self, project_name):
        self.current_project = self.projects.get(project_name)

    def emptyline(self):
        """Handles an empty line (does nothing)."""
        pass

    def default(self, line):
        if self.current_project:
            task = self.current_project.task(line.strip())
        else:
            task = None

        if task:
            self._print_task(task)
            return

        cmd.Cmd.default(self, line)

    def do_project(self, line):
        """Switch to a project with the provided name."""
        line = line.strip()
        if not line:
            self._print_projects()
            return

        self._set_current_project(line)

        if not self.current_project:
            self._error("No project found named '{0}'".format(line))
        else:
            self._success("Switched to project '{0}'".format(
                self.current_project.name))

    def do_metrics(self, line):
        """Print out metrics available for the current project."""
        if not self.current_project:
            self._error("Please select a project first using the 'project' "
                        "command")
            return

        for metric_name in sorted(self.current_project.metrics):
            m = self.current_project.metrics[metric_name]
            if m.desc:
                self._print("* {0} ({1}) -> {2}".format(metric_name,
                                                        m.units.display_name(),
                                                        m.desc))
            else:
                self._print("* {0} ({1})".format(metric_name,
                                                 m.units.display_name()))

        self._print("")

    def do_print(self, line):
        """Print information on an existing task or project."""
        if not line:
            self._print_project()
        else:
            self._print_task(line)

    def do_exit(self, line):
        """Exit the application."""
        return True

    def do_quit(self, line):
        """Exit the application."""
        return True

    def do_task(self, line):
        """Create a task or edit an existing task."""
        line = line.strip()
        if not line:
            self._error("You must specify a task to create or update.\n"
                        "Usage: task [TASK_NAME]")
            return

        tokens = shlex.split(line)
        task_name = tokens[0]
        args = tokens[1:]

        if len(args):
            success = self._update_task(task_name, args)
        else:
            success = self._update_task_interactive(task_name)

        if success:
            self._success("Task updated")

    def _update_task_interactive(self, task_name):
        return False

    def _update_task(self, task_name, args):
        metrics = []
        for i in range(0, len(args), 2):
            metric_name = args[i]
            value_str = args[i + 1]
            metric = self._get_metric(metric_name)
            if not metric:
                self._error("Invalid metric: " + metric_name)
                return

            try:
                value = metric.units.parse(value_str)
            except ParsingError as e:
                self._error(str(e))
                return

            metrics.append((metric, value))

        self.current_project.update_task(task_name, metrics=metrics)

        return True

    def _get_metric(self, metric_name):
        # First, try to use the string as is:
        metric = self.current_project.metric(metric_name)
        if metric:
            return metric

        metric_name = metric_name.replace("_", " ").title()
        return self.current_project.metric(metric_name)

    def _print_project(self):
        p = self.current_project
        # TODO - More content will come later
        self._print("Project: " + p.name)

    def _print_projects(self):
        self._title("Projects")
        for project in Project.projects():
            self._print("* {0} (nickname: {1}) -> {2}".format(project.name,
                                                              project.nickname,
                                                              project.desc))
        self._print("\n")

    def _print_task(self, task):
        output = ["Created: " + str(task.created)]
        output.append("Last Updated: " + str(task.last_updated))
        output.append("\n")
        for data_point in task.data_points:
            output.append(" {0} -> {1}".format(data_point.metric,
                                               data_point.value))

        self._print("\n".join(output) + "\n")

    def _title(self, line):
        self._print("\n" + line)
        self._print("-" * min(len(line), 80) + "\n")

    def _success(self, msg):
        self._print(msg, 'green')
        print()

    def _warning(self, msg):
        self._print("Warning: " + msg, "yellow")
        print()

    def _error(self, msg):
        self._print("Error: " + msg, "red")
        print()

    def _print(self, msg=None, color=None):
        if msg and color and self.use_color:
            msg = colored(msg, color)

        print(msg, file=self.stdout)


def main():
    parser = argparse.ArgumentParser(description="Maxify programmer time "
                                                 "tracker client")
    parser.add_argument("-p",
                        "--project",
                        help="Name of project to start tracking time against "
                             "once the client starts. For a project belonging "
                             "to a particular organization, prefix the name "
                             "with the organization, like: scopetastic/maxify.")
    parser.add_argument("-f",
                        "--data-file",
                        default="maxify.db",
                        help="Path to Maxify data file. By default, this is "
                             "'maxify.db' in the current directory.")

    args = parser.parse_args()

    colorama.init()
    import_config()
    Repository.init(args.data_file)

    interpreter = MaxifyCmd()
    interpreter.cmdloop(args.project)


if __name__ == "__main__":
    main()
