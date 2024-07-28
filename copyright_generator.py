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

import argparse
import configparser
from dataclasses import dataclass, asdict
import datetime
from enum import Enum
import json
import logging
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import traceback
from typing import Dict, List, Set

LOGGER = logging.getLogger(__name__)

LOGGER_FORMATTER = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
LOGGER_HANDLER = logging.StreamHandler()
LOGGER_HANDLER.setFormatter(LOGGER_FORMATTER)

LOGGER.addHandler(LOGGER_HANDLER)

PLATFORM_SYSTEM = platform.system()

PATH_SEPARATOR = '/'

PROJECT_COPYRIGHT_FILE_NAME = ".copyright"
METADATA_FILE_NAME = ".copyright_meta"
DEFAULT_COPYRIGHT_FILE_NAME = "COPYRIGHT.txt"

LICENSE_URLS_SECTION_NAME = "license_urls"

LICENSE_FILE_NAME_START_WITH_LIST = [
	"license",
	# Common misspelling, see https://github.com/Charlie85270/tail-kit/blob/main/LICENCE.md.
	"licence",

	# Haven't found an example of these yet as of 5/21/2024 1:35 PM, so excluding them (especially since 'lisense' could flag a false-positive, being close to a potential library name).
	# "lisence",
	# "lisense",
]

# TODO: Compile list of common copyleft licenses and add warnings for them. (GPL, Mozilla Public License 2.0, CDDL, etc).

class CopyrightKeys(Enum):
	SOURCE_URL = "source_url"
	UPSTREAM_NAME = "upstream_name"
	UPSTREAM_CONTACT_NAME = "upstream_contact_name"
	UPSTREAM_CONTACT_EMAIL = "upstream_contact_email"
	LICENSE = "license"
	COPYRIGHT = "copyright"
	THIRDPARTY_FOLDER_PATH = "thirdparty_folder_path"

	PROJECT_NAME = "name"
	PROJECT_YEAR = "year"
	PROJECT_AUTHOR = "author"
	PROJECT_AUTHOR_YEAR = "author_year"
	PROJECT_COPYRIGHT = "copyright"
	PROJECT_LICENSE = "license"

@dataclass
class CopyrightMetadataFile:
	name: str
	author: str
	license: str
	year: str | None = None
	author_year: str | None = None
	copyright: str | None = None

	def to_config(self):
		dataclass_dictionary = asdict(self)

		keys_to_remove = []
		for key, value in dataclass_dictionary.items():
			if value == None:
				keys_to_remove.append(key)

		for key in keys_to_remove:
			dataclass_dictionary.pop(key)

		return_config = configparser.ConfigParser()
		return_config.read_dict({ 
			'root': dataclass_dictionary
		})

		return return_config

def parse_copyright_meta_file(copyright_meta_file_path : Path):
	config = configparser.ConfigParser()

	try:
		config.read(copyright_meta_file_path)
	except configparser.MissingSectionHeaderError:
		# There was not a valid header in the file, so we need to append on to the file and re-parse it.
		with open(copyright_meta_file_path, 'r') as meta_file:
			config.read_string("[root]\n" + meta_file.read())

	return config

def parse_license_file_copyright_lines(license_file_path : Path):
	copyright_lines : List[str] = []

	with open(license_file_path, 'r') as license_file:
		for line in license_file.readlines():
			if line.strip().lower().startswith("copyright"):
				line_split = line.split(')', 2)

				if len(line_split) == 2:
					copyright_lines.append(line_split[-1].strip())

	return copyright_lines

def parse_copyright_years(string : str):
	year_string_list : List[str] = []
	can_read_year_number = True
	current_year_number = ""
	for character in string.replace('\\n', '\n'):
		if character.isdigit():
			if len(current_year_number) > 4:
				can_read_year_number = False
			
			if can_read_year_number:
				current_year_number += character
		else:
			can_read_year_number = True

			if len(current_year_number) == 4:
				year_string_list.append(current_year_number)

			current_year_number = ""

	all_years_valid = True
	if len(year_string_list) > 0:
		for year in year_string_list:
			try:
				year_int = int(year)

				# TODO: This is relatively reasonable, but not exactly a catch-all for mis-parsing files. Currently, it's better than doing nothing, but not by much.
				if year_int < 1900 or year_int > datetime.datetime.now().year:
					all_years_valid = False
					break
			except:
				pass

	return (year_string_list, all_years_valid)

def parse_project_author_year_and_project_year_from_license(license_file_path : str | os.PathLike):
	project_author_year_string : str | None = None
	project_year_string : str | None = None

	license_file_path = Path(license_file_path)
	if license_file_path.exists():
		if project_year_string == None and project_author_year_string == None:
			# Attempt to parse copyright lines from license file.
			copyright_lines = parse_license_file_copyright_lines(license_file_path)

			if len(copyright_lines) > 0:
				project_author_year_string = ', '.join(copyright_lines)

		if project_year_string == None and project_author_year_string == None:
			# Attempt to parse project year string from license file.
			try:
				with open(license_file_path, 'r') as license_file:
					copyright_years, all_years_valid = parse_copyright_years(license_file.read())

					if len(copyright_years) > 0 and all_years_valid:
						project_year_string = '-'.join(copyright_years)
			except:
				pass

	return (project_author_year_string, project_year_string)

def main():
	parser = argparse.ArgumentParser(prog='CopyrightGenerator', description='Generates a COPYRIGHT file using the Debian copyright format.')
	parser.add_argument('-i', '--input', dest="copyright", default=PROJECT_COPYRIGHT_FILE_NAME, help="Path to the project copyright file for the current project. Default: " + PROJECT_COPYRIGHT_FILE_NAME)
	parser.add_argument('-c', '--copyright', default=PROJECT_COPYRIGHT_FILE_NAME, help="Path to the project copyright file for the current project. Default: " + PROJECT_COPYRIGHT_FILE_NAME)
	parser.add_argument('-o', '--output', default=DEFAULT_COPYRIGHT_FILE_NAME, help="Path to the output copyright file for the entire project. Default: " + DEFAULT_COPYRIGHT_FILE_NAME)
	parser.add_argument('-l', '--list', action='store_true', help="Whether to list the unique copyright types used in the project. Default: False")
	parser.add_argument('--disable_npm', action='store_true', help="Whether to disable NPM checking. Default: False")
	parser.add_argument('--disable_pip_licenses', action='store_true', help="Whether to disable pip-licenses checking. Default: False")
	parser.add_argument('--disable_gradle', action='store_true', help="Whether to disable Gradle checking. Default: False")
	parser.add_argument('--disable_nuget_license', action='store_true', help="Whether to disable nuget-license checking. Default: False")
	parser.add_argument('-q', '--quiet', action='store_true', help="Whether to disable information and warning logging. Default: False")

	args = parser.parse_args()

	if args.quiet:
		class QuietFilter(logging.Filter):
			def filter(self, record):
				return record.levelname not in [logging.getLevelName(logging.INFO), logging.getLevelName(logging.DEBUG), logging.getLevelName(logging.WARN), logging.getLevelName(logging.WARNING)]

		LOGGER.addFilter(QuietFilter())

	project_copyright_file_path = Path(args.copyright)
	output_copyright_file_path = Path(args.output)

	# If the '.copyright' file doesn't exist, write a default one.
	if not project_copyright_file_path.exists():
		with open(project_copyright_file_path, 'w') as copyright_file:
			copyright_file.write(CopyrightKeys.SOURCE_URL.value + ' = https://www.example.com/software/project' + '\n')
			copyright_file.write(CopyrightKeys.UPSTREAM_NAME.value + ' = SOFTware' + '\n')
			copyright_file.write(CopyrightKeys.UPSTREAM_CONTACT_NAME.value + ' = John Doe' + '\n')
			copyright_file.write(CopyrightKeys.UPSTREAM_CONTACT_EMAIL.value + ' = john.doe@example.com' + '\n')
			copyright_file.write(CopyrightKeys.THIRDPARTY_FOLDER_PATH.value + ' = thirdparty' + '\n')

	# Attempt to parse the '.copyright' file.
	copyright_config = configparser.ConfigParser()
	try:
		copyright_config.read(project_copyright_file_path)
	except configparser.MissingSectionHeaderError:
		# There was not a valid header in the file, so we need to prepend one to the file and re-parse it.
		with open(project_copyright_file_path, 'r') as copyright_file:
			copyright_config.read_string("[root]\n" + copyright_file.read())

	first_section = copyright_config.sections()[0]

	source_url = copyright_config.get(first_section, CopyrightKeys.SOURCE_URL.value)
	upstream_name = copyright_config.get(first_section, CopyrightKeys.UPSTREAM_NAME.value)
	upstream_contact_name = copyright_config.get(first_section, CopyrightKeys.UPSTREAM_CONTACT_NAME.value)
	upstream_contact_email = copyright_config.get(first_section, CopyrightKeys.UPSTREAM_CONTACT_EMAIL.value)
	thirdparty_folder_path_string = copyright_config.get(first_section, CopyrightKeys.THIRDPARTY_FOLDER_PATH.value)

	thirdparty_folder_path = Path(thirdparty_folder_path_string)
	if not thirdparty_folder_path.exists():
		LOGGER.warning("Folder '" + str(thirdparty_folder_path.absolute()) + "' does not exist.")

		# LOGGER.error("Folder '" + str(thirdparty_folder_path.absolute()) + "' does not exist, cannot generate copyright.")
		# exit()

	license_meta_file_dictionary : Dict[Path, Path | CopyrightMetadataFile] = {}

	# NPM and Node.js Handler.
	# TODO: Detect other frameworks other than Node.js.
	# TODO: Detect and ignore TypeScript type modules.
	if not args.disable_npm and shutil.which("npm") != None and Path(Path.cwd(), "package.json").exists():
		ran_npx_successfully = False

		try:
			process : subprocess.CompletedProcess[bytes] = subprocess.run(["npm", "exec", "--no", "--", "license-checker", "--json"], capture_output=True)

			stdout_string = process.stdout.decode()
			stderr_string = process.stderr.decode()
			if len(stderr_string) == 0:
				license_checker_output_json : Dict[str, Dict[str, str]] = json.loads(stdout_string)

				for project_namespace, project_dictionary in license_checker_output_json.items():
					if "licenses" in project_dictionary:
						project_author_year_string : str | None = None
						project_year_string : str | None = None

						if "licenseFile" in project_dictionary:
							project_author_year_string, project_year_string = parse_project_author_year_and_project_year_from_license(project_dictionary["licenseFile"])

						project_folder_absolute_path_string = project_dictionary["path"]
						project_folder_relative_path_string = project_folder_absolute_path_string.removeprefix(str(Path.cwd()))

						# Remove any leading file separators.
						while project_folder_relative_path_string.startswith('/') or project_folder_relative_path_string.startswith('\\'):
							project_folder_relative_path_string = project_folder_relative_path_string[1:]

						license_meta_file_dictionary[Path(project_folder_relative_path_string)] = CopyrightMetadataFile(name=project_namespace, author=project_dictionary.get("publisher", None), license=project_dictionary["licenses"], year=project_year_string, author_year=project_author_year_string)
					else:
						LOGGER.warning("Project '" + str(project_namespace) + "' missing license in dictionary '" + str(project_dictionary) + "'")

				ran_npx_successfully = True
			else:
				LOGGER.error("Caught error running license-checker: " + str(stderr_string).strip())
		except Exception:
			LOGGER.error("Caught exception while running npx:")
			LOGGER.error(traceback.format_exc())

		if not ran_npx_successfully:
			LOGGER.warning("Could not find 'license-checker'. Install using 'npm install --save-dev license-checker'.")

	# pip-licenses Handler.
	if not args.disable_pip_licenses:
		pipenv_prefix : List[str] = []
		python_prefix : List[str] | None = None

		if python_prefix == None and shutil.which("pipenv") != None and Path(Path.cwd(), "Pipfile").exists():
			pipenv_prefix = ["pipenv", "run"]

		if python_prefix == None and shutil.which("python") != None:
			python_prefix = ["python"]

		if python_prefix == None and shutil.which("python3") != None:
			python_prefix = ["python3"]

		if python_prefix != None:
			is_python_project = False

			# Check if requirements.txt exists.
			if not is_python_project:
				for file_path in Path.cwd().iterdir():
					if file_path.is_file() and file_path.name.startswith("requirements"):
						is_python_project = True

			# Check if any Python files exist (WARNING: Least reliable).
			if not is_python_project:
				for file_path in Path.cwd().iterdir():
					if file_path.is_file() and file_path.suffix == ".py":
						is_python_project = True
						break

			if is_python_project:
				pip_license_parameters = ["--with-authors", "--with-license-file", "--format=json"]
				ran_pip_licenses_successfully = False

				for command_list in [
					# Attempt to run the pip-licenses bin using the current Pipenv.
					pipenv_prefix + ["pip-licenses"] + pip_license_parameters if len(pipenv_prefix) > 0 else None,
					# Attempt to run the module using the Python version from Pipenv.
					pipenv_prefix + python_prefix + ["-m", "pip-licenses"] + pip_license_parameters,
				]:
					if ran_pip_licenses_successfully:
						break

					if command_list != None:
						# Attempt to use pip-licenses to get licensing information.
						process : subprocess.CompletedProcess[bytes] = subprocess.run(command_list, capture_output=True)

						stdout_string = process.stdout.decode()
						stderr_string = process.stderr.decode()
						if len(stderr_string) == 0:
							project_dictionary_list : List[Dict[str, str]] = json.loads(stdout_string)

							for project_dictionary in project_dictionary_list:
								project_author_year_string : str | None = None
								project_year_string : str | None = None

								if "LicenseFile" in project_dictionary:
									project_author_year_string, project_year_string = parse_project_author_year_and_project_year_from_license(project_dictionary["LicenseFile"])

								# Remove everything before site-packages if it exists.
								license_path = Path("site-packages" + project_dictionary["LicenseFile"].split("site-packages")[-1])

								license_meta_file_dictionary[license_path] = CopyrightMetadataFile(name=project_dictionary["Name"], author=project_dictionary.get("Author", None), license=project_dictionary["License"], year=project_year_string, author_year=project_author_year_string)

							break
						else:
							LOGGER.error("Caught error running pip-licenses: " + str(stderr_string).strip())

	# Gradle Handler.
	if not args.disable_gradle:
		gradlew_path : Path | None = None
		if PLATFORM_SYSTEM == "Windows":
			gradlew_path = Path(Path.cwd(), "gradlew.bat")
		elif PLATFORM_SYSTEM == "Linux":
			gradlew_path = Path(Path.cwd(), "gradlew")
		elif PLATFORM_SYSTEM == "Darwin":
			# TODO: Untested
			gradlew_path = Path(Path.cwd(), "gradlew")

		if gradlew_path != None:
			gradle_license_report_path  = Path(Path.cwd(), "build", "reports", "dependency-license", "report.json")
			if gradlew_path.exists() and gradlew_path.is_file():
				ran_gradle_successfully = False

				try:
					process : subprocess.CompletedProcess[bytes] = subprocess.run([str(gradlew_path), "generateLicenseReport"], capture_output=True)

					stdout_string = process.stdout.decode()
					stderr_string = process.stderr.decode()
					if len(stderr_string) == 0:
						if gradle_license_report_path.exists():
							ran_gradle_successfully = True
							with open(gradle_license_report_path, 'r') as gradle_license_report_file:
								dependencies_dictionary_list : Dict[str, List[Dict[str, str]]] = json.loads(gradle_license_report_file.read())

								if 'dependencies' in dependencies_dictionary_list:
									dependencies_list = dependencies_dictionary_list['dependencies']
									for dependency_dictionary in dependencies_list:
										if "moduleLicense" in dependency_dictionary:
											# TODO: Convert human-readable license to SPDX code, maybe use https://github.com/spdx/license-list-data.
											license_meta_file_dictionary[Path(dependency_dictionary["moduleName"])] = CopyrightMetadataFile(name=dependency_dictionary["moduleName"], author=None, license=dependency_dictionary["moduleLicense"], year=None, author_year=None)
										else:
											LOGGER.warning("Could not find license for module '" + dependency_dictionary["moduleName"] + "'. Skipping.")
								else:
									LOGGER.warning("Did not find 'dependencies' key in JSON file at '" + str(gradle_license_report_path) + "'. Is the file malformed?")
						else:
							LOGGER.warning("Could not find report JSON file at '" + str(gradle_license_report_path) + "', ensure your renderers include a " + 'JsonReportRenderer("report.json")' + " item.")
					else:
						LOGGER.error("Caught error running " + str(gradlew_path) + ": " + str(stderr_string).strip())
				except Exception:
					LOGGER.error("Caught exception while running " + str(gradlew_path) + ": ")
					LOGGER.error(traceback.format_exc())					

				if not ran_gradle_successfully:
					LOGGER.warning("Could not find 'Gradle-License-Report'. Install by following the instructions at 'https://github.com/jk1/Gradle-License-Report?tab=readme-ov-file#usage'. Ensure you have the 'configurations' config option set correctly for your project type (for Android: '" + 'configurations = arrayOf("ALL", "releaseRuntimeClasspath")' + "').")
		else:
			LOGGER.error("Unsupported platform for Gradle check: " + str(PLATFORM_SYSTEM))

	# nuget-license Handler.
	if not args.disable_nuget_license:
		nuget_license_prefix : List[str] | None = None

		if nuget_license_prefix == None and shutil.which("nuget-license") != None:
			nuget_license_prefix = ["nuget-license"]

		if nuget_license_prefix != None:
			project_file : Path | None = None

			# TODO: Which order do we want to check these in to get the best result?

			# Check if any .sln file exists.
			if project_file == None:
				for file_path in Path.cwd().iterdir():
					if file_path.is_file() and file_path.name.endswith(".sln"):
						project_file = file_path

			# Check if any .csproj file exists.
			if project_file == None:
				for file_path in Path.cwd().iterdir():
					if file_path.is_file() and file_path.name.endswith(".csproj"):
						project_file = file_path

			if project_file != None:
				nuget_license_parameters = ["-i", str(project_file.absolute()), "-o", "jsonPretty"]

				command_list = nuget_license_prefix + nuget_license_parameters

				# Attempt to use nuget-license to get licensing information.
				process : subprocess.CompletedProcess[bytes] = subprocess.run(command_list, capture_output=True)

				stdout_string = process.stdout.decode()
				stderr_string = process.stderr.decode()
				if len(stderr_string) == 0:
					project_dictionary_list : List[Dict[str, str]] = json.loads(stdout_string)

					for project_dictionary in project_dictionary_list:
						project_copyright_string : str | None = None

						if "Copyright" in project_dictionary:
							project_copyright_string = ""

							# TODO: More robust parsing of the line.
							found_alpha_character = False
							for character in project_dictionary["Copyright"].replace("Copyright", "").strip():
								if not found_alpha_character and (character.isalpha() or character.isdigit()):
									found_alpha_character = True

								if found_alpha_character:
									project_copyright_string += character

						if "License" in project_dictionary:
							license_meta_file_dictionary[Path(project_dictionary["PackageId"])] = CopyrightMetadataFile(name=project_dictionary["PackageId"], author=project_dictionary.get("Authors", None), license=project_dictionary["License"], copyright=project_copyright_string)
						else:
							LOGGER.warning("Could not find license for package '" + project_dictionary["PackageId"] + "'. Skipping.")
				else:
					LOGGER.error("Caught error running nuget-license: " + str(stderr_string).strip())

	folder_path_list : List[Path] = []

	# Add the base directory as the first folder to check. Don't want to use Path.cwd() as it is the absolute file path to the project.
	folder_path_list.append(Path())

	# Add all the folders inside the thirdparty folder directory sorted. This won't be exactly as specified by the OS (due to this not being a natural sort), but it should be close enough.
	if thirdparty_folder_path.exists():
		folder_path_list += sorted(thirdparty_folder_path.iterdir())

	# Iterate each folder inside 'thirdparty'.
	while len(folder_path_list) > 0:
		thirdparty_project_folder_path = folder_path_list.pop()
		if not thirdparty_project_folder_path.exists():
			LOGGER.error("Folder '" + str(thirdparty_project_folder_path.absolute()) + "' does not exist, skipping.")
			continue

		# Find the metadata file for the current directory if it exists.
		meta_file_path = Path(thirdparty_project_folder_path, METADATA_FILE_NAME)
		if meta_file_path.exists():
			config = parse_copyright_meta_file(copyright_meta_file_path=meta_file_path)

			# Check if we have any license URLs. If we do, download the files from the links.
			for section in config.sections():
				if section == LICENSE_URLS_SECTION_NAME:
					for url in dict(config.items(section)).values():
						import urllib.request

						file_name : str | None = None

						if file_name == None:
							with urllib.request.urlopen(url) as response:
								response : urllib.request.HTTPResponse
								content_disposition = response.info()['Content-Disposition']

								# Attempt to extract file name from headers.
								if content_disposition != None:
									m = urllib.request.Message()
									m['content-type'] = content_disposition
									file_name = m.get_param("filename")

						# Finally, if we do not have a file name, attempt to extract file name from final path part.
						if file_name == None:
							file_name = Path(url).name

						# Download the file to the current thirdparty folder.
						urllib.request.urlretrieve(url, Path(thirdparty_project_folder_path, file_name))

			license_file_path : Path | None = None

			# Attempt to find license file in thirdparty project folder.
			for copyright_file in thirdparty_project_folder_path.iterdir():
				copyright_lower_file_name = copyright_file.name.lower()

				for license_file_name_starts_with in LICENSE_FILE_NAME_START_WITH_LIST:
					if copyright_lower_file_name.startswith(license_file_name_starts_with.lower()):
						license_file_path = copyright_file

			if license_file_path != None:
				# Link the license file path to the meta file path.
				license_meta_file_dictionary[license_file_path] = meta_file_path
			else:
				LOGGER.error("Folder '" + str(thirdparty_project_folder_path.absolute()) + "' does not contain a findable license file.")
		else:
			LOGGER.error("Folder '" + str(thirdparty_project_folder_path.absolute()) + "' does not contain a findable copyright '" + str(METADATA_FILE_NAME) + "' meta file.")

	unique_licenses : Set[str] | None = None
	if args.list:
		unique_licenses = set()

	with open(output_copyright_file_path, 'w') as copyright_file:
		def write_line(line : str | None = None, end : str | None = '\n'):
			copyright_file.write((line if line != None else "") + (end if end != None else ""))

		# Header ( https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/#:~:text=5.1.1.%20example%20header%20stanza )
		write_line("Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/")
		write_line("Source: " + source_url)
		write_line("Upstream-Name: " + upstream_name)
		write_line("Upstream-Contact: " + upstream_contact_name + " <" + upstream_contact_email + ">")

		write_line()

		for license_file_path, meta_file in license_meta_file_dictionary.items():
			if isinstance(meta_file, Path):
				config = parse_copyright_meta_file(copyright_meta_file_path=meta_file)
			elif isinstance(meta_file, CopyrightMetadataFile):
				config = meta_file.to_config()
			else:
				LOGGER.warning("Invalid meta_file for license file path '" + str(license_file_path) + "': " + str(meta_file) + "'.")
				continue

			first_section = config.sections()[0]

			project_name = config.get(first_section, CopyrightKeys.PROJECT_NAME.value)

			project_year : str | None = None
			project_author : str | None = None
			project_author_year : str | None = None
			project_copyright : str | None = None

			if config.has_option(first_section, CopyrightKeys.PROJECT_YEAR.value):
				project_year = config.get(first_section, CopyrightKeys.PROJECT_YEAR.value)

			if config.has_option(first_section, CopyrightKeys.PROJECT_AUTHOR.value):
				project_author = config.get(first_section, CopyrightKeys.PROJECT_AUTHOR.value)

			if config.has_option(first_section, CopyrightKeys.PROJECT_AUTHOR_YEAR.value):
				project_author_year = config.get(first_section, CopyrightKeys.PROJECT_AUTHOR_YEAR.value)

			if config.has_option(first_section, CopyrightKeys.PROJECT_COPYRIGHT.value):
				project_copyright = config.get(first_section, CopyrightKeys.PROJECT_COPYRIGHT.value)

			# if project_year == None and project_author_year == None:
			# 	print("No year for project '" + project_name + "'.")

			if project_copyright == None:
				if project_author_year == None and project_author == None:
					LOGGER.warning("No author for project '" + project_name + "'. Defaulting to project name for copyright.")
					project_author = project_name

				if project_author_year == None and project_year == None and project_author == None:
					LOGGER.warning("No year nor author for project '" + project_name + "'. Config: " + str(meta_file.__dict__))

			project_license = config.get(first_section, CopyrightKeys.PROJECT_LICENSE.value)
			if unique_licenses != None:
				unique_licenses.add(project_license)

			write_line("Files: ")
			write_line(" " + str(license_file_path.parent).replace('\\', PATH_SEPARATOR) + "/*")
			write_line("Comment: " + project_name)

			if project_copyright != None:
				write_line(("" if project_copyright.startswith("Copyright: ") else "Copyright: ") + str(project_copyright).replace('\\n', '\n'))
			else:
				if project_author_year != None:
					write_line("Copyright: " + str(project_author_year).replace('\\n', '\n'))
				else:
					write_line("Copyright:" + (" " + project_year if project_year != None else "") + (" " + project_author if project_author != None else ""))

			write_line("License: " + project_license)

			write_line()

	# Remove all filters for any final outputs.
	for filter in LOGGER.filters:
		LOGGER.removeFilter(filter)

	if unique_licenses != None:
		LOGGER.info(sorted(list(unique_licenses)))

	return 0

if __name__ == '__main__':
	sys.exit(main())