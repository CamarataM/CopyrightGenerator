#!/usr/bin/env python3
"""
This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <http://unlicense.org/>
"""

from pathlib import Path
import platform
import subprocess
import sys
from typing import List

readme_file_path = Path("README.md")

def main():
	readme_lines : List[str]
	with open(readme_file_path, 'r') as input_file:
		readme_lines = input_file.readlines()

	if readme_lines != None:
		with open(readme_file_path, 'w') as output_file:
			in_usage_help = False
			for line in readme_lines:
				output_line : str | None = line.strip()

				if in_usage_help:
					if output_line != '<!-- POST-USAGE-HELP -->':
						output_line = None
					else:
						# Finally, write the new help section right above the finish line.
						platform_system = platform.system()

						process : subprocess.CompletedProcess[bytes] | None = None
						if platform_system == "Windows":
							process = subprocess.run(["python", "copyright_generator.py", "--help"], capture_output=True)
						elif platform_system == "Linux":
							process = subprocess.run(["python3", "copyright_generator.py", "--help"], capture_output=True)
						else:
							print("Unsupported platform system '" + str(platform_system) + "'.")

						ran_successfully = False
						if process != None:
							ran_successfully = True

							stdout_string = process.stdout.decode()
							stderr_string = process.stderr.decode()

							if len(stderr_string) == 0:
								output_file.write('```' + '\n')
	
								for stdout_line in stdout_string.splitlines():
									output_file.write(stdout_line + '\n')

								output_file.write('```' + '\n')
							else:
								print("Got error from running process:")
								print(stderr_string)
						if not ran_successfully:
							print("Failed to run copyright_generator successfully.")

						in_usage_help = False
				elif output_line == '<!-- PRE-USAGE-HELP -->':
					in_usage_help = True

				if output_line != None:
					output_file.write(output_line + '\n')
	else:
		print("ERROR: Could not find readme file.")

	return 0

if __name__ == '__main__':
	sys.exit(main())