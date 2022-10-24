import shutil
import sys
from pathlib import Path
import re


# rename file or folder, return new path(<class 'pathlib.WindowsPath'>)
def rename(path: Path, name):
    new_path = path.with_stem(name)
    path.rename(new_path)

    return new_path


# transliterate Cyrillic characters in Latin, replace all punctuation signs, return new name (str)
def normalize(name: str):
    PATTERN = "\W"
    CYRILLIC_SYMBOLS = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяєіїґ"
    TRANSLATION = (
        "a", "b", "v", "g", "d", "e", "e", "j", "z", "i", "j", "k", "l", "m", "n", "o", "p", "r", "s", "t", "u",
        "f", "h", "ts", "ch", "sh", "sch", "", "y", "", "e", "yu", "ya", "je", "i", "ji", "g")

    TRANS = {}

    for c, l in zip(CYRILLIC_SYMBOLS, TRANSLATION):
        TRANS[ord(c)] = l
        TRANS[ord(c.upper())] = l.upper()
        name = name.translate(TRANS)
        normalize_name = re.sub(PATTERN, "_", name)

    return normalize_name


# recursively scan directory collect all nested paths in list, return list with paths (<class 'pathlib.WindowsPath'>)
def scan_dir(path: Path, ignore: list):
    all_paths = []
    empty_for_ignor = []

    for every_path in path.iterdir():

        if every_path.is_dir():
            all_paths.append(every_path)
            all_paths.extend(scan_dir(every_path, empty_for_ignor))

        elif every_path.is_file():
            all_paths.append(every_path)

    return all_paths


# recursively scan directory collect all file paths in list, return list with paths (<class 'pathlib.WindowsPath'>)
def collect_files_paths(path: Path, ignore: list):
    all_files_paths = []
    empty_list_for_ignor = []

    for every_path in path.iterdir():

        if every_path.is_dir():
            all_files_paths.extend(scan_dir(every_path, empty_list_for_ignor))

        elif every_path.is_file():
            all_files_paths.append(every_path)

    return all_files_paths


# return dict key: type (folders name) value: list of all file paths this type
def sort_files(paths_list, type_dict: dict, ):
    result = {"unknown_extensions": set(),
              "known_extensions": set()
              }

    sorted_dict = dict.fromkeys(type_dict.keys())

    for key in sorted_dict.keys():
        sorted_dict[key] = []

    for path in paths_list:
        for file_type, extensions in type_dict.items():
            if path.suffix.upper() in extensions:
                sorted_dict[file_type].append(path)
                result["known_extensions"].add(path.suffix)
                continue
            else:
                result["unknown_extensions"].add(path.suffix)
                continue

    result["unknown_extensions"] = result["unknown_extensions"] ^ result["known_extensions"]
    result["unknown_extensions"] = list(result["unknown_extensions"])
    result["known_extensions"] = list(result["known_extensions"])

    list_for_pop = []
    for key, value in sorted_dict.items():
        if not value:
            list_for_pop.append(key)

    for key_for_pop in list_for_pop:
        del sorted_dict[key_for_pop]

    return sorted_dict, result


# create folders, named as keys in dictionary, return dict (folder_path : list_of_files)
def create_folder(dictionary, path):
    updated_dictionary = {}
    for folder_name in dictionary:
        Path(path, folder_name).mkdir(exist_ok=True)
        updated_dictionary[Path(path, folder_name)] = dictionary[folder_name]

    return updated_dictionary


def replace_repack(dictionary):
    count_for_rename = 1
    for folder_path, list_of_files in dictionary.items():
        for file in list_of_files:
            already_in_folder = []

            for path in folder_path.iterdir():
                already_in_folder.append(path.name)

            try:
                shutil.unpack_archive(file, folder_path)
            except shutil.ReadError:
                if file.name in already_in_folder:
                    warming_name = f"{file.stem}_!!!_({count_for_rename}){file.suffix}"
                    shutil.move(file, Path(folder_path, warming_name))
                    count_for_rename += 1
                else:
                    shutil.move(file, Path(folder_path, file.name))


# remove empty folders,
def remove_empty(path: Path, ignore: list):
    all_folders = []
    empty_for_ignor = []

    for i in path.iterdir():

        if i.is_file():
            continue

        if i.is_dir():
            all_folders.append(i)

            all_folders.extend(remove_empty(i, empty_for_ignor))

    all_folders.reverse()

    for folder in all_folders:

        try:
            folder.rmdir()
        except OSError:
            continue

    return all_folders


def main(types_dictionary: dict, origin_path: Path, dest_path, ignore: list):

    print(f"\nStart to organize the directory:\n"
          f"{original_path}")

    if dest_path == origin_path:
        new_name_dir = normalize(origin_path.stem)
        origin_path = rename(origin_path, new_name_dir)
        dest_path = origin_path

        print(f"\nDestination path didn't specify.\n"
              f"In the directory:\n"
              f"{original_path}\n"
              f"will be created {len(ignor_folders_list)} folders:\n"
              f" {folders_names}\n"
              f"\nIf folders named: {folders_names} already exist,\n"
              f"all the files in this folders will be ignored,\n"
              f"but files from another folders from the directory:\n"
              f"{original_path}\n"
              f"will be replace in this folders\n"
              )

    else:

        print(f"\nDestination path is {destination_path}\n"
              f"In the directory will be created {len(ignor_folders_list)} folders:\n"
              f" {folders_names}\n")

        new_name_dir = normalize(origin_path.stem)

        origin_path = rename(origin_path, new_name_dir)

    paths_for_rename = scan_dir(origin_path, ignore)

    paths_for_rename.reverse()

    for p in paths_for_rename:
        rename(p, normalize(p.stem))

    files_paths = collect_files_paths(origin_path, ignore)

    sorted_paths, res = sort_files(files_paths, types_dictionary)

    dict_for_replace = create_folder(sorted_paths, dest_path)

    replace_repack(dict_for_replace)

    remove_empty(origin_path, ignore)

    # print report of found files and extensions:
    print(f"\nDirectory {original_path}\n"
          f"was contained files with extensions:")

    for title, contain in res.items():
        print("\n")
        print("{:-^75}".format(title))

        count = 1
        for item in contain:
            item = str(item)

            if count <= 5:
                print("{:^15}".format(item), end="")
                count += 1

            else:
                count = 1
                print("\n")
    print("\n")
    print(f"\nDirectory {original_path}\n"
          f"was contained this types of files:")

    for title, contain in sorted_paths.items():
        print("\n")
        print("{:-^75}".format(title))

        count = 1
        for item in contain:
            item = Path(item).name

            if count <= 3:
                print("{:^25}".format(item), end=",")
                count += 1

            else:
                count = 1
                print("\n")

    return sorted_paths, res


types = {"documents": ('.DOC', '.DOCX', '.TXT', '.PDF', '.XLSX', '.PPTX'),
         "image": ('.JPEG', '.PNG', '.JPG', '.SVG', '.BMP'),
         "video": ('.AVI', '.MP4', '.MOV', '.MKV'),
         "music": ('.MP3', '.OGG', '.WAV', '.AMR'),
         "archive": ('.ZIP', '.GZ', '.TAR')
         }

ignor_folders_list = list(types.keys())

folders_names = "´, `".join(ignor_folders_list)

original_path = Path(sys.argv[1])

try:
    destination_path = Path(sys.argv[2])
except IndexError:
    destination_path = Path(original_path)


if __name__ == '__main__':

    main(types, original_path, destination_path, ignor_folders_list)

