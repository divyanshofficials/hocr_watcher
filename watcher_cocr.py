# -*- coding: utf-8 -*-
"""
Created on Wed Feb 10 21:17:51 2021

@author: Divyansh
"""

import os
import time

from watchdog.observers import Observer

from watchdog.events import RegexMatchingEventHandler

import AbbyyOnlineSdk


processor = None

def setup_processor():
    if "ABBYY_APPID" in os.environ:
        processor.ApplicationId = os.environ["ABBYY_APPID"]

    if "ABBYY_PWD" in os.environ:
        processor.Password = os.environ["ABBYY_PWD"]

    # Proxy settings
    if "http_proxy" in os.environ:
        proxy_string = os.environ["http_proxy"]
        print("Using http proxy at {}".format(proxy_string))
        processor.Proxies["http"] = proxy_string

    if "https_proxy" in os.environ:
        proxy_string = os.environ["https_proxy"]
        print("Using https proxy at {}".format(proxy_string))
        processor.Proxies["https"] = proxy_string


# Recognize a file at filePath and save result to resultFilePath
def recognize_file(file_path, result_file_path, language, output_format):
    print("Uploading..")
    settings = AbbyyOnlineSdk.ProcessingSettings()
    settings.Language = language
    settings.OutputFormat = output_format
    task = processor.process_image(file_path, settings)
    if task is None:
        print("Error")
        return
    if task.Status == "NotEnoughCredits":
        print("Not enough credits to process the document. Please add more pages to your application's account.")
        return

    print("Id = {}".format(task.Id))
    print("Status = {}".format(task.Status))

    # Wait for the task to be completed
    print("Waiting..")
    # Note: it's recommended that your application waits at least 2 seconds
    # before making the first getTaskStatus request and also between such requests
    # for the same task. Making requests more often will not improve your
    # application performance.
    # Note: if your application queues several files and waits for them
    # it's recommended that you use listFinishedTasks instead (which is described
    # at https://ocrsdk.com/documentation/apireference/listFinishedTasks/).

    while task.is_active():
        time.sleep(5)
        print(".")
        task = processor.get_task_status(task)

    print("Status = {}".format(task.Status))

    if task.Status == "Completed":
        if task.DownloadUrl is not None:
            processor.download_result(task, result_file_path)
            print("Result was written to {}".format(result_file_path))
    else:
        print("Error processing task")



def main_process(src,lang='English',output_format = 'txt'):
    global processor
    processor = AbbyyOnlineSdk.AbbyyOnlineSdk()
    setup_processor()
    filename = src.replace('.jpg','.txt')
    filename = filename.replace('images','dst')
    dst = filename
    if os.path.isfile(src):
        recognize_file(src, dst, lang, output_format)
        return True
    else:
        print("No such file: {}".format(src))
        return False


class ImagesEventHandler(RegexMatchingEventHandler):
    IMAGES_REGEX = [r".*[^_thumbnail]\.jpg$"]
    def __init__(self):
        super().__init__(self.IMAGES_REGEX)

    def on_created(self, event):
        self.process(event)

    def process(self, event):
        src = event.src_path
        op = main_process(src=src)
        if op:
            print('Success')
        else:
            print('Failure')





class ImagesWatcher:
    def __init__(self, src_path):
        self.__src_path = src_path
        self.__event_handler = ImagesEventHandler()
        self.__event_observer = Observer()

    def run(self):
        self.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def start(self):
        self.__schedule()
        self.__event_observer.start()

    def stop(self):
        self.__event_observer.stop()
        self.__event_observer.join()

    def __schedule(self):
        self.__event_observer.schedule(
            self.__event_handler,
            self.__src_path,
            recursive=True
        )

if __name__ == "__main__":
    src_path = "images"
    src_path = os.path.join(os.getcwd(),src_path)
    print(src_path)
    ImagesWatcher(src_path).run()