import asyncio
import logging
import os
import pathlib
import random
import string
import time

from tempfile import TemporaryDirectory


HERE = pathlib.Path(__file__).parent.absolute()
with open(HERE / "soffice-registry.xcu") as f:
    SOFFICE_CONFIG = f.read()


def create_job_id():
    return "".join(
        [random.choice(string.ascii_lowercase + string.digits) for _ in range(5)]
    )


class PdfCreator:
    def __init__(self, working_directory, concurrency=2):
        self.working_directory = working_directory
        self.semaphore = asyncio.Semaphore(concurrency)
        self.ongoing_tasks = {}

    def status(self, job_id):
        jobs = set(os.listdir(self.working_directory))
        if job_id not in jobs:
            return "invalid"

        else:
            if os.path.exists(
                os.path.join(self.working_directory, job_id, "output", "document.pdf")
            ):
                return "ok"
            else:
                return "pending"

    def task(self, job_id):
        """Get the task for `job_id`"""
        return self.ongoing_tasks[job_id]

    def convert(self, document):
        job_id = create_job_id()
        job_dir = os.path.join(self.working_directory, job_id)
        output_dir = os.path.join(job_dir, "output")
        os.makedirs(output_dir)

        _, extension = os.path.splitext(document["filename"])
        fname = os.path.join(job_dir, "document%s" % extension)

        with open(fname, "wb") as f:
            f.write(document["body"])

        task = asyncio.create_task(
            self._convert_to_pdf(
                output_dir,
                job_id,
                fname,
            )
        )
        self.ongoing_tasks[job_id] = task

        return job_id

    async def _convert_to_pdf(self, output_dir, task_id, input_fname):
        try:
            async with self.semaphore:
                with TemporaryDirectory() as soffice_dir:
                    tick = time.time()
                    logging.info(f"[{task_id}] started")

                    os.makedirs(os.path.join(soffice_dir, "user"))
                    with open(
                        os.path.join(soffice_dir, "user/registrymodifications.xcu"), "w"
                    ) as f:
                        f.write(SOFFICE_CONFIG)

                    proc = await asyncio.create_subprocess_exec(
                        "/usr/local/bin/soffice",
                        f"-env:UserInstallation=file://{soffice_dir}",
                        "--headless",
                        "--convert-to",
                        "pdf",
                        "--outdir",
                        output_dir,
                        input_fname,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )

                    try:
                        stdout, stderr = await asyncio.wait_for(
                            proc.communicate(), timeout=60
                        )
                    except asyncio.TimeoutError:
                        logging.error(f"[{task_id}] timed out")
                        return

                    logging.info(f"[{task_id}] exited with {proc.returncode}")
                    if stdout:
                        logging.debug(f"[{task_id} stdout]\n{stdout.decode()}")
                    if stderr:
                        logging.debug(f"[{task_id} stderr]\n{stderr.decode()}")

        finally:
            tock = time.time()
            logging.debug(f"[{task_id}] took %i seconds" % (tock - tick))
