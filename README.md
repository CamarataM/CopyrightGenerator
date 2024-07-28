# CopyrightGenerator

**CopyrightGenerator** is a small Python script which generates `debian/copyright` files based on [Debian Policy 4.7.0.0](https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/).

This software, when provided with the correct metadata files, produces a file containing the copyright information of scanned sub-projects.

This software is licensed under [Unlicense](https://unlicense.org/).

## Metadata Files
### .copyright
A project contains one '**.copyright**' file. An example can be found in the repository. The fields for this file are outlined below and maps to the '[Fields](https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/#fields)' section of the `debian/copyright` specification:

- **source_url**: A URL to the software's source repository. **Required**.
- **upstream_name**: The name of the software. **Required**.
- **upstream_contact_name**: The name of the primary contact for the software. **Required**.
- **upstream_contact_email**: The email of the primary contact for the software. **Required**.
- **thirdparty_folder_path**: The path to the thirdparty folder to scan for sub-projects. **Required**.

### .copyright_meta
A project contains many '**.copyright_meta**' files, one for each thirdparty project with separate copyright information. The fields for this file are outlined below and maps to the '[File stanza \(repeatable\)](https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/#files-stanza)' section of the `debian/copyright` specification:
- **name**: The name of the thirdparty project. **Required**.
- **year**: The copyright year of the thirdparty project. Is automatically formatted and combined with the **author** field. **Optional**.
- **author**: The author of the thirdparty project. Is automatically formatted and combined with the **year** field. **Optional**.
- **author_year**: The author and year of the thirdparty project. Is **not** automatically formatted and will be used instead of the **year** or **author** fields. **Optional**.
- **copyright**: The full copyright string of the thirdparty project. Is **not** automatically formatted and will be used instead of the **year**, **author**, and **author_year** fields. Note: Will still prepend 'Copyright: ' to ensure matches the format DEP-5 expects. **Optional**.
- **license**: The license of the thirdparty project. **Required**.

## Usage
<!-- TODO: Test on lower Python 3 versions. The absolute minimum is 3.5 for the typing features we use, although we would have to use the old typing.Union form to get below 3.10: https://docs.python.org/3/library/typing.html#typing.Union -->
Run 'copyright_generator.py' using a Python 3 version 3.10 or above with either the current working directory set to the root of the project containing the '**.copyright**' file or with the **-i** CLI parameter set to the path of the root of the project containing the '**.copyright**' file.

```
$ python copyright_generator.py --help
usage: CopyrightGenerator [-h] [-i COPYRIGHT] [-c COPYRIGHT] [-o OUTPUT] [-l] [--disable_npm] [--disable_pip_licenses]
                          [--disable_gradle] [-q]

Generates a COPYRIGHT file using the Debian copyright format.

options:
  -h, --help            show this help message and exit
  -i COPYRIGHT, --input COPYRIGHT
                        Path to the project copyright file for the current project. Default: .copyright
  -c COPYRIGHT, --copyright COPYRIGHT
                        Path to the project copyright file for the current project. Default: .copyright
  -o OUTPUT, --output OUTPUT
                        Path to the output copyright file for the entire project. Default: COPYRIGHT.txt
  -l, --list            Whether to list the unique copyright types used in the project. Default: False
  --disable_npm         Whether to disable NPM checking. Default: False
  --disable_pip_licenses
                        Whether to disable pip-license checking. Default: False
  --disable_gradle      Whether to disable Gradle checking. Default: False
  -q, --quiet           Whether to disable information and warning logging. Default: False
```

## Known Issues
- The glob patterns for project files is imprecise and incorrect for pip-license, and Gradle (as those typically store their dependencies in external locations). This makes their glob pattern default to being every file in the project directory, which is incorrect.
- The following of the `debian/copyright` specification isn't exact / tested against.

## Contributing
All contributions welcome, although I intend to keep the project as simple as possible with improvements to unit-testing and validation being greatly appreciated. As recommended by [unlicense.org](https://unlicense.org/#unlicensing-contributions), contributions **must** include a statement such as:
```
I dedicate any and all copyright interest in this software to the
public domain. I make this dedication for the benefit of the public at
large and to the detriment of my heirs and successors. I intend this
dedication to be an overt act of relinquishment in perpetuity of all
present and future rights to this software under copyright law.
```

## License
This software is licensed under [Unlicense](https://unlicense.org/).