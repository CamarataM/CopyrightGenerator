#!/usr/bin/env python3
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