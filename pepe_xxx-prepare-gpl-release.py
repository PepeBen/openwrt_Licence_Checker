#!/usr/bin/env python3
# Copyright (C) 2022 Ben Pepe
import os
from shutil import rmtree
import glob
import argparse
import re
import sys
###### Variables ######
###### Functions ######


def find_line(path, substring):
    with open(path, 'r') as f:
        string = f.read()
        string = string.splitlines()
        for line in string:
            if substring in line:
                return line


def str_to_regex_str(input_str):
    regex_string = ''
    special_char_list = ['.', '\\', '+', '?', '$', '^',
                         '(', ')', '[', ']', '{', '}', '*', '|']
    # Convert special character in regext to literal's
    for i in range(0, len(input_str)):
        if input_str[i] in special_char_list:
            regex_string += '\\' + input_str[i]
        else:
            regex_string += input_str[i]

    return regex_string


def find_file_regex(package_name, version):
    regex_string = ''
    regex_string += str_to_regex_str(package_name)
    regex_string += '(\_|\W)'
    regex_string += str_to_regex_str(version)
    regex_expression = ('^%s.*$' % regex_string)
    for file in os.scandir(tarball_dir):
        if (re.match(regex_expression, file.name) and
                os.path.isfile(os.path.join(tarball_dir, file.name))):
            return [file.name]

    return ''


def get_current_version(zzz_dir, key_word):
    current_version = []
    for dir in os.scandir(os.path.join(zzz_dir, 'buildap/target')):
        target_path = 'buildap/target/' + dir.name + '/xxx_config.py'
        version_find = find_line(os.path.join(zzz_dir, target_path), key_word)
        version_find = version_find.split('=')[1].strip("'")
        if version_find not in current_version:
            current_version.append(version_find)

    return current_version


def delete_not_in_list(target_dir, file_list):
    for file in os.scandir(target_dir):
        if file.name not in file_list and os.path.isdir(os.path.join(target_dir, file.name)):
            if opts.verbose_bol:
                print("Removing ", file.name)
            rmtree(os.path.join(target_dir, file.name))

        elif file.name not in file_list and os.path.isfile(os.path.join(target_dir, file.name)):
            if opts.verbose_bol:
                print("Removing ", file.name)
            os.remove(os.path.join(target_dir, file.name))

    return


def delete_git(zzz_dir):
    for root, dirs, files in os.walk(zzz_dir):
        for target in glob.glob(os.path.join(root, ".git*")):
            if os.path.isdir(target):
                if opts.verbose_bol:
                    print("Removing ", target)
                rmtree(target)

            elif os.path.isfile(target):
                if opts.verbose_bol:
                    print("Removing ", target)
                os.remove(target)

    return


def delete_sensitive_docs(zzz_dir):
    directory_list = ['xxx-tools', 'buildap', 'docker']
    file_list = ['README.md', 'Readme.txt']
    for dir_buff in directory_list:
        dir_buff = os.path.join(zzz_dir, dir_buff)
        for file in file_list:
            file = os.path.join(dir_buff, file)
            if os.path.isfile(file):
                if opts.verbose_bol:
                    print("Removing ", file)
                os.remove(file)

    return


def delete_xxx(zzz_dir, chipcode_dir):
    key_word = 'xxx_chipcode_ver'
    xxx_ver = get_current_version(zzz_dir, key_word)
    for dir in os.scandir(chipcode_dir):
        if dir.name not in xxx_ver and os.path.isdir(os.path.join(chipcode_dir, dir.name)):
            if opts.verbose_bol:
                print("Removing ", dir.name)
            rmtree(os.path.join(chipcode_dir, dir.name))

        elif dir.name not in xxx_ver and os.path.isfile(os.path.join(chipcode_dir, dir.name)):
            if opts.verbose_bol:
                print("Removing ", dir.name)
            os.remove(os.path.join(chipcode_dir, dir.name))

        else:
            for dir in xxx_ver:
                current_dir = os.path.join(chipcode_dir, dir)
                if opts.verbose_bol:
                    print("Removing files from ", current_dir)

                chipcode_list = ['codexxxxx']
                delete_not_in_list(current_dir, chipcode_list)

    return


def delete_tarballs(zzz_dir, tarball_dir):
    package_list = []
    try:
        with open(opts.package_list_dir, 'r') as read_file:
            while True:
                # Get package data
                package_source_name = read_file.readline().rstrip('\n')
                package_name = read_file.readline().rstrip('\n')
                version = read_file.readline().rstrip('\n')
                proprietary = read_file.readline().rstrip('\n')
                # If end of file then exit while loop
                if not package_name:
                    break
                if proprietary != '1':
                    if package_source_name:
                        package_list.append(package_source_name)
                    else:
                        package_list.append(find_file_regex(package_name, version))
        key_word = 'toolchain_pack'
        for toolchain in get_current_version(zzz_dir, key_word):
            package_list += find_file_regex(toolchain, '')
        delete_not_in_list(tarball_dir, package_list)
        return
    except IOError as e:
        print ("I/O error({0}): {1}".format(e.errno, e.strerror))
        raise
    except:
        print ("Unexpected error:", sys.exc_info()[0])
        raise


def edit_docker_config(script_dir):
    buff = []
    with open(os.path.join(script_dir, 'docker_config.py'), "r") as read_file:
        for line in read_file:
            if 'dns' in line:
                # Replace atkk's dns ip address with google's public dns server ip addresses
                buff.append("dns=['8.8.8.8','8.8.4.4']\n")
            else:
                buff.append(line)

    with open(os.path.join(script_dir, 'docker_config.py'), "w") as write_file:
        write_file.writelines(buff)

    return


def remove_files(zzz_dir, chipcode_dir, script_dir, tarball_dir):
    """
    This removes all git and proprietary files
    """
    script_list = ['buildap', 'buildap.py', 'buildap_docker.py', 'helpers.py', 'docker_user_remap', 'docker_config.py']
    delete_not_in_list(script_dir, script_list)

    edit_docker_config(script_dir)

    if os.path.exists(os.path.join(zzz_dir, "xxxprop")):
        if opts.verbose_bol:
            print("Removing xxxprop")
        rmtree(os.path.join(zzz_dir, "xxxprop"))

    if os.path.exists(os.path.join(zzz_dir, "xxxagent")):
        if opts.verbose_bol:
            print("Removing xxxagent")
        rmtree(os.path.join(zzz_dir, "xxxagent"))

    delete_git(zzz_dir)

    delete_sensitive_docs(zzz_dir)

    if opts.verbose_bol:
        print("Removing files from ", chipcode_dir)

    delete_xxx(zzz_dir, chipcode_dir)

    if opts.verbose_bol:
        print("Removing files from ", tarball_dir)

    delete_tarballs(zzz_dir, tarball_dir)

    return


def get_files(verbose_git, release_name, zzz_dir, script_dir, tarball_dir):
    # clone repository if no source directory was specified
    if opts.which_option == 'download':
        args = "git clone %s -b %s --recursive git@git-xxx.co.jp:xxx/xxx.git %s" % (verbose_git, opts.tag_name, release_name)
        os.system(args)

    if opts.verbose_bol:
        print("Entering ", zzz_dir)
    os.chdir(zzz_dir)
    args = "git clone %s git@git-xxx.co.jp:xxx/xxx_scripts.git" % (verbose_git)
    os.system(args)

    if opts.verbose_bol:
        print("Entering ", tarball_dir)

    os.mkdir(tarball_dir)
    os.chdir(tarball_dir)
    args = "rsync -av --progress rsync://xxx.yyy.zzz.co.jp:/tarballs ."
    os.system(args)

    return


def parse_program_arguments():
    """
    Uses argparse to display help text
    """
    parser = argparse.ArgumentParser(description='Use xxx-prepare-gpl-release to prepare a publicly releasable version of the xxx repository')

    subparsers = parser.add_subparsers()
    download_parser = subparsers.add_parser('download', help="")
    download_parser.add_argument('--verbose', '-v',
                                 action='store_true',
                                 default=False,
                                 dest='verbose_bol',
                                 help='verbose will print out the codes movement to the terminal')
    download_parser.add_argument('--model', '-m',
                                 action='store',
                                 dest='target_model',
                                 required=True,
                                 help='make the gpl tarball for target model',)
    download_parser.add_argument('--tag', '-t',
                                 action='store',
                                 dest='tag_name',
                                 required=True,
                                 help='tag is used to specify the tag/branch')
    download_parser.add_argument('--dest', '-d',
                                 action='store',
                                 dest='dest_path',
                                 default=".",
                                 help='dest is used to specify the full path to the final destination of the output tarball, do not use hanging forward slashes')
    download_parser.add_argument('package_list_dir',
                                 action='store',
                                 type=str,
                                 help='full path to the list "package-full-list" in the output directory of the xxx repository, that list is used to filter tarballs')
    download_parser.set_defaults(which_option='download')

    local_parser = subparsers.add_parser('local', help="")
    local_parser.add_argument('--verbose', '-v',
                              action='store_true',
                              default=False,
                              dest='verbose_bol',
                              help='verbose will print out the codes movement to the terminal')
    local_parser.add_argument('--src', '-s',
                              action='store',
                              dest='src_path',
                              required=True,
                              default='',
                              help='src is used to specify the full path to the source of the repository to prepare for gpl release, do not use hanging forward slashes')
    local_parser.add_argument('--dest', '-d',
                              action='store',
                              dest='dest_path',
                              default=".",
                              help='dest is used to specify the full path to the final destination of the output tarball, do not use hanging forward slashes')
    local_parser.add_argument('package_list_dir',
                              action='store',
                              type=str,
                              help='full path to the list "package-full-list" in the output directory of the xxx repository, that list is used to filter tarballs')
    local_parser.set_defaults(which_option='local')

    # This displays help message and exits the script if no option or arguments are passed
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    return parser.parse_known_args()


###### Main ######
if __name__ == "__main__":

    opts, extra = parse_program_arguments()

    if opts.verbose_bol:
        verbose_git = ""
        verbose_tar = "-v"
    else:
        verbose_git = "--quiet"
        verbose_tar = ""

    if opts.verbose_bol:
        if opts.which_option == 'download':
            print("tag/branch: ", opts.tag_name)
        if opts.which_option == 'local':
            print("source repository: ", opts.src_path)

    # Set generated tarbal name
    if opts.which_option == 'local':
        # Uses the source directory name to generate the output tarball's name
        release_name = opts.src_path.split('/').pop()
    elif opts.which_option == 'download':
        # Uses tag and model to generate the output tarball's name
        tag = opts.tag_name.replace("/", "-")
        model = opts.target_model.replace("/", "-")
        release_name = "xxx-gpl-release-%s-%s" % (model, tag)

    # destination_dir determines where the output tarball will go
    # The destination directory is set to '.' by default.
    destination_dir = opts.dest_path
    # Set paths for xxx repository and one directory up from xxx repository
    if opts.which_option == 'local':
        # Use source path provided as the reference path for other paths
        zzz_dir = opts.src_path
        # Set directory to call tar
        home_dir = opts.src_path.rstrip(release_name)
        print('home dir :', home_dir)
    elif opts.which_option == 'download':
        # Use the current directory as the place to clone xxx repository
        home_dir = os.getcwd()
        zzz_dir = os.path.join(home_dir, release_name)
    chipcode_dir = os.path.join(zzz_dir, 'xxx/chipcode')
    script_dir = os.path.join(zzz_dir, 'xxx_scripts')
    tarball_dir = os.path.join(zzz_dir, 'tarballs')

    # Download files that are needed
    get_files(verbose_git, release_name, zzz_dir, script_dir, tarball_dir)

    # Remove files that are not to be publicaly released
    remove_files(zzz_dir, chipcode_dir, script_dir, tarball_dir)

    # Move to one directory up to tar the xxx repository
    os.chdir(home_dir)
    args = "tar %s -cJf %s/%s.tar.xz %s" % (verbose_tar, destination_dir, release_name, release_name)
    os.system(args)

    # If source directory is provided, do not remove it after tarball is created.
    # The source directory may be used for other purposes.
    if opts.which_option == 'download':
        rmtree(zzz_dir)

    if opts.verbose_bol:
        print("done")
