from assetutilities.common.file_edit_concatenate import FileConcatenate
from assetutilities.common.file_edit_split import FileSplit
from assetutilities.common.file_management import FileManagement

fm = FileManagement()
fe_c = FileConcatenate()
fe_s = FileSplit()


class FileEdit:
    def __init__(self) -> None:
        pass

    def router(self, cfg):
        if cfg["edit_type"] == "concatenate":
            fe_c.concatenate_files(cfg)
        elif cfg["edit_type"] == "split":
            fe_s.router(cfg)

        return cfg
