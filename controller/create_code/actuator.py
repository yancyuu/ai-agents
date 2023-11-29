import sys
import time

from controller.create_code.prompts import Prompts
from controller.create_code.utils import generate_folder, write_file
from common_sdk.logging.logger import logger

defaultmodel = "gpt-4-0613"

class Actuator:

    def __init__(self) -> None:
        self.prompts = Prompts()


    def run(self, prompt, generate_folder_path="generated"): 
        code_res = {}      
        # plan shared_deps
        logger.info("--------shared_deps---------")
    
        shared_deps = self.prompts.plan(prompt, stream_handler)
        logger.info(shared_deps)
        write_file(f"{generate_folder_path}/shared_deps.md", shared_deps)
        logger.info("--------shared_deps---------")

        # specify file_paths
        logger.info("--------specify_filePaths---------")
        file_paths = self.prompts.specify_file_paths(prompt, shared_deps)
        logger.info(file_paths)
        logger.info("--------file_paths---------")

        # loop through file_paths array and generate code for each file
        for file_path in file_paths:
            file_path = f"{generate_folder_path}/{file_path}"  # just append prefix
            logger.info(f"--------generate_code: {file_path} ---------")
            start_time = time.time()
            def stream_handler(chunk):
                end_time = time.time()
                sys.stdout.write("\r \033[93mChars streamed\033[0m: {}. \033[93mChars per second\033[0m: {:.2f}".format(stream_handler.count, stream_handler.count / (end_time - start_time)))
                sys.stdout.flush()
                stream_handler.count += len(chunk)
            stream_handler.count = 0
            stream_handler.onComplete = lambda x: sys.stdout.write("\033[0m\n") # remove the stdout line when streaming is complete
            code = self.prompts.generate_code_sync(prompt, shared_deps, file_path, stream_handler)
            logger.info(code)
            logger.info(f"--------generate_code: {file_path} ---------")
            code_res[file_path] = code
            
        logger.info("-------- done!---------")

    def run_local(self, prompt, generate_folder_path="generated"):
        # create generateFolder folder if doesnt exist
        generate_folder(generate_folder_path)

        # plan shared_deps
        logger.info("--------shared_deps---------")
        with open(f"{generate_folder_path}/shared_deps.md", "wb") as f:

            start_time = time.time()
            

            shared_deps = self.prompts.plan(prompt, stream_handler)
        logger.info(shared_deps)
        write_file(f"{generate_folder_path}/shared_deps.md", shared_deps)
        logger.info("--------shared_deps---------")

        # specify file_paths
        logger.info("--------specify_filePaths---------")
        file_paths = self.prompts.specify_file_paths(prompt, shared_deps)
        logger.info(file_paths)
        logger.info("--------file_paths---------")

        # loop through file_paths array and generate code for each file
        for file_path in file_paths:
            file_path = f"{generate_folder_path}/{file_path}"  # just append prefix
            logger.info(f"--------generate_code: {file_path} ---------")

            start_time = time.time()
            def stream_handler(chunk):
                end_time = time.time()
                sys.stdout.write("\r \033[93mChars streamed\033[0m: {}. \033[93mChars per second\033[0m: {:.2f}".format(stream_handler.count, stream_handler.count / (end_time - start_time)))
                sys.stdout.flush()
                stream_handler.count += len(chunk)
            stream_handler.count = 0
            stream_handler.onComplete = lambda x: sys.stdout.write("\033[0m\n") # remove the stdout line when streaming is complete
            code = self.prompts.generate_code_sync(prompt, shared_deps, file_path, stream_handler)
            logger.info(code)
            logger.info(f"--------generate_code: {file_path} ---------")
            # create file with code content
            write_file(file_path, code)
            
        logger.info("-------- done!---------")
