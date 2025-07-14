# Standard library imports
import itertools
import os
import shutil

# Reader imports
from assetutilities.common.utilities import is_file_valid_func


class FileConcatenate:
    def __init__(self) -> None:
        pass

    def router(self, cfg):
        if cfg["edit_type"] == "concatenate":
            self.concatenate_files(cfg)

    def concatenate_files(self, cfg):
        if cfg["concatenate_type"] == "array":
            cfg, batch_filename = self.concatenate_files_array(cfg)
        elif cfg["concatenate_type"] == "2d_array":
            cfg, batch_filename = self.concatenate_files_2d_array(cfg)

        return cfg, batch_filename

    def concatenate_files_array(self, cfg):
        output_filename_array = []
        batch_filename_array = []
        for idx in range(0, len(cfg["input"])):
            input_set = cfg["input"][idx]
            output_files = {"ext": [], "no_ext": []}
            input_file_groups = input_set["input_files"]
            input_idx_output_filename_array = []
            for input_file_group_indx in range(0, len(input_file_groups)):
                input_file_group = input_file_groups[input_file_group_indx]
                output_filename = (
                    input_set["output_basename"]
                    + "_"
                    + input_set["input_file_labels"][input_file_group_indx]
                )
                input_idx_output_filename_array.append(output_filename)

                output_dir = input_set.get("output_dir", None)
                if output_dir is None:
                    output_dir = cfg["Analysis"]["analysis_root_folder"]
                else:
                    output_dir = os.path.join(
                        cfg["Analysis"]["analysis_root_folder"], output_dir
                    )
                output_filename_path = os.path.join(output_dir, output_filename)

                file_extension = input_set.get("file_extension", "dat")
                output_filename_path = os.path.join(
                    output_dir, output_filename + "." + file_extension
                )
                output_filename_path_no_ext = os.path.join(output_dir, output_filename)
                output_files["ext"].append(output_filename_path)
                output_files["no_ext"].append(output_filename_path_no_ext)

                cfg = self.concatenate_one_set(
                    cfg, input_file_group, output_filename_path
                )

            output_filename_array.append(input_idx_output_filename_array)
            batch_filename = self.prepare_custom_batch(
                cfg, input_set, idx, output_files
            )

        batch_filename_array.append(batch_filename)

        cfg[cfg["basename"]] = {
            "output_filename": output_filename_array,
            "batch_filename": batch_filename_array,
        }

        return cfg, batch_filename

    def concatenate_one_set(self, cfg, input_files, output_filename_path):
        analysis_root_folder = cfg["Analysis"]["analysis_root_folder"]
        with open(output_filename_path, "wb") as wfd:
            for f in input_files:
                file_is_valid, valid_file = is_file_valid_func(f, analysis_root_folder)

                with open(valid_file, "rb") as fd:
                    shutil.copyfileobj(fd, wfd)

        return cfg

    def concatenate_files_2d_array(self, cfg):
        for input_set_idx in range(0, len(cfg["input"])):
            input_set = cfg["input"][input_set_idx]
            output_files = {"ext": [], "no_ext": []}
            output_dir = input_set.get("output_dir", None)
            if output_dir is None:
                output_dir = cfg["Analysis"]["analysis_root_folder"]
            else:
                output_dir = os.path.join(
                    cfg["Analysis"]["analysis_root_folder"], output_dir
                )
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)

            file_extension = input_set.get("file_extension", "dat")

            input_file_labels = input_set.get("input_file_labels")
            input_files_2d = input_set["input_files"]

            input_files_2d_permutations = list(itertools.product(*input_files_2d))
            input_files_labels_permutations = list(
                itertools.product(*input_file_labels)
            )

            for set_2d_idx in range(0, len(input_files_2d_permutations)):
                output_filename = input_set["output_basename"]
                file_array = list(input_files_2d_permutations[set_2d_idx])
                label_array = list(input_files_labels_permutations[set_2d_idx])

                for label in label_array:
                    if label == "":
                        label_separator = ""
                    else:
                        label_separator = "_"
                    output_filename = output_filename + label_separator + label

                output_filename_path = os.path.join(
                    output_dir, output_filename + "." + file_extension
                )
                output_filename_path_no_ext = os.path.join(output_dir, output_filename)
                output_files["ext"].append(output_filename_path)
                output_files["no_ext"].append(output_filename_path_no_ext)

                cfg = self.concatenate_one_set(cfg, file_array, output_filename_path)

            batch_filename = self.prepare_custom_batch(
                cfg, input_set, input_set_idx, output_files
            )

        return cfg, batch_filename

    def prepare_custom_batch(self, cfg, input_set, idx, output_files):
        batch_cfg = input_set.get("batch", None)
        batch_filename = os.path.join(
            cfg["Analysis"]["analysis_root_folder"],
            cfg["Analysis"]["file_name"] + "_" + str(idx) + ".bat",
        )
        if batch_cfg is not None and batch_cfg["flag"]:
            with open(batch_filename, "w") as the_file:
                if batch_cfg["extension"]:
                    for output_file_name in output_files["ext"]:
                        the_file.write(
                            batch_cfg["content"] + " " + output_file_name + "\n"
                        )
                else:
                    for output_file_name in output_files["no_ext"]:
                        the_file.write(
                            batch_cfg["content"] + " " + output_file_name + "\n"
                        )

        return batch_filename
