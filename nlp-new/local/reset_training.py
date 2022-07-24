import os
import logging
import shutil

# messages
deleted_model = "Deleted the model files for the given app and object."
cannot_delete = "Couldn't remove the trained model files directory."
model_not_found = "Model folder does not exist. Try training a model."

def reset(model_dir):
    if os.path.isdir(model_dir):
        try:
            shutil.rmtree(model_dir)
            msg = {"msg":deleted_model}
            logging.info(deleted_model)
            return msg
        except:
            logging.info(cannot_delete)
            msg = {"msg":cannot_delete}
            return msg
    else:
        logging.info(model_not_found)
        msg = {"msg":model_not_found}
        return msg