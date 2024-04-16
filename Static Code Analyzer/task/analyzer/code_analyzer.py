import ast
import operator
import os
import re
import sys


class ExceptionHandler(Exception):
    line_Number = 0

    def __init__(self, lineNumber, code, message):
        self.line_Number = lineNumber
        self.code = code
        self.message = f"Line {self.line_Number}: S{self.code} {message}"
        super().__init__(self.message)


def longLineError(line, cont):
    if len(line) > 79:
        raise ExceptionHandler(cont, "001", "Too long")


def indentationError(line, cont):
    if (len(line) - len(line.lstrip(' '))) % 4 != 0:
        raise ExceptionHandler(cont, "002", "Indentation is not a multiple of four")


def semicolonError(line, cont):
    if '#' in line and line.split('#')[0].strip().endswith(';'):
        raise ExceptionHandler(cont, "003", "Unnecessary semicolon")
    if '#' not in line and line.strip().endswith(';'):
        raise ExceptionHandler(cont, "003", "Unnecessary semicolon")


def spacesCommentsError(line, cont):
    if not line.startswith('#') and '#' in line and not line.split('#')[0].endswith('  '):
        raise ExceptionHandler(cont, "004", "At least two spaces required before inline comments")


def todoError(line, cont):
    if '#' in line and 'todo' in line.split('#')[1].lower():
        raise ExceptionHandler(cont, "005", "TODO found")


def blankLinesError(listLines):
    cont = 0
    for index in range(len(listLines)):
        if listLines[index] == '':
            cont += 1
            if cont > 2:
                raise ExceptionHandler(index + 2, "006", "More than two blank lines preceding a code line")
        else:
            cont = 0


def spacesClassError(line, cont):
    template = '^class\s{2,}'
    templateDef = '^\s{4}def\s{2,}\w*'

    if re.match(template, line):
        raise ExceptionHandler(cont, "007", "Too many spaces after 'class'")

    if re.match(templateDef, line):
        raise ExceptionHandler(cont, "007", "Too many spaces after 'def'")


def nameClassError(line, cont):
    templateClass = '^class\s{1}[a-z]'

    if re.match(templateClass, line):
        raise ExceptionHandler(cont, "008", "Class name 'user' should use CamelCase")


def functionNameError(line, cont):
    template = '^\s{0,4}def\s{1}[A-Z]\w*'

    if re.match(template, line):
        raise ExceptionHandler(cont, "009",
                               f"Function name {re.search(template, line).group().lstrip('def ')} should use "
                               f"snake_case")


def argumentDefaultNameError(archive, path):
    if archive != path:
        string = f'{path}\{archive}'
    else:
        string = archive

    with open(string, 'r') as file:
        tree = ast.parse(file.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for a in node.args.defaults:
                    if type(a) == ast.List or type(a) == ast.Dict or type(a) == ast.Set:
                        raise ExceptionHandler(a.lineno, "012",
                                               f"The default argument value is mutable.")


def argumentNameError(archive, path):
    if archive != path:
        string = f'{path}\{archive}'
    else:
        string = archive
    with open(string, 'r') as file:
        tree = ast.parse(file.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for a in node.args.args:
                    if re.match('[A-Z]+', a.arg):
                        raise ExceptionHandler(a.lineno, "010",
                                               f"Argument name {a.arg} should be written in snake_case")


def variableNameError(archive, path):
    if archive != path:
        string = f'{path}\{archive}'
    else:
        string = archive
    with open(string, 'r') as file:
        tree = ast.parse(file.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for a in node.body:
                    if isinstance(a, ast.Assign):
                        for b in a.targets:
                            if isinstance(b, ast.Name):
                                if re.match('[A-Z]+', b.id):
                                    error_temp = ExceptionHandler(a.lineno, "011",
                                                                  f"Variable {b.id} in function should be snake_case")

                                    yield error_temp


args = sys.argv
path_or_arch = args[1]
list_paths = []
archive = ""

try:
    list_paths = os.listdir(path_or_arch)
except NotADirectoryError as err:
    archive = path_or_arch

list_lines_dict = {}

if len(list_paths) > 0:
    for arch in list_paths:
        list_temp = []
        with open(path_or_arch + '\\' + arch, 'r') as file:
            for i in file:
                list_temp.append(i.replace("\n", ''))

        list_lines_dict[arch] = list_temp
else:
    with open(archive, 'r') as file:
        list_temp = []
        for i in file:
            list_temp.append(i.replace("\n", ''))
        list_lines_dict[archive] = list_temp

dict_errors = {}
exceptionList = [longLineError, indentationError, semicolonError, spacesCommentsError, todoError,
                 spacesClassError, nameClassError, functionNameError]

for arc in list_lines_dict.keys():
    blankLines = 0
    for exception in exceptionList:

        for line, i in enumerate(list_lines_dict[arc], start=1):
            try:
                exception(i, line)
            except ExceptionHandler as error:
                dict_errors[error.message] = error.line_Number
    try:
        blankLinesError(list_lines_dict[arc])
    except ExceptionHandler as error:
        dict_errors[error.message] = error.line_Number

    try:
        argumentDefaultNameError(arc, path_or_arch)
    except ExceptionHandler as error:
        dict_errors[error.message] = error.line_Number

    try:
        argumentNameError(arc, path_or_arch)
    except ExceptionHandler as error:
        dict_errors[error.message] = error.line_Number

    result = variableNameError(arc, path_or_arch)
    while True:
        try:
            error = next(result)
            dict_errors[error.message] = error.line_Number
        except StopIteration:
            break

    dict_sorted = dict(sorted(dict_errors.items(), key=operator.itemgetter(1)))

    if len(archive) > 0:
        for message in dict_sorted.keys():
            print(f'{archive}: {message}')
    else:
        for message in dict_sorted.keys():
            print(f'{path_or_arch}\{arc}: {message}')
    dict_errors = {}
