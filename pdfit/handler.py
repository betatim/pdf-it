import json
import logging

from tornado import websocket
from tornado.log import app_log
from tornado.web import RequestHandler, HTTPError


class BaseHandler(RequestHandler):
    @property
    def pdf_creator(self):
        return self.application.pdf_creator

    def get_json_body(self):
        """Return the body of the request as JSON data."""
        if not self.request.body:
            return None
        body = self.request.body.strip().decode("utf-8")
        try:
            model = json.loads(body)
        except Exception:
            app_log.debug("Bad JSON: %r", body)
            app_log.error("Couldn't parse JSON", exc_info=True)
            raise HTTPError(400, "Invalid JSON in body of request")
        return model


class PingHandler(BaseHandler):
    async def get(self):
        self.finish("pong")


class WelcomePage(BaseHandler):
    def get(self):
        self.render("templates/upload.html")


class ConversionHandler(BaseHandler):
    async def post(self):
        """Create a new conversion task"""
        if "document" not in self.request.files:
            raise HTTPError(422, "Need a document")

        document = self.request.files["document"][0]
        logging.info(
            "uploaded file %s %s %i bytes"
            % (document["filename"], document["content_type"], len(document["body"]))
        )

        job_id = self.pdf_creator.convert(document)

        # Send JSON to the robots
        if self.request.headers["accept"] == "application/json":
            self.write(
                {
                    "status": "pending",
                    "job_id": job_id,
                    "message": "document pending",
                }
            )

        # HTML for everyone else
        else:
            self.redirect(f"/convert/{job_id}", status=303)

    async def get(self, job_id):
        """Get the status of a conversion job"""
        status = self.pdf_creator.status(job_id)

        if self.request.headers["accept"] == "application/json":
            if status == "not-found":
                self.set_status(404)
                self.write(
                    {
                        "status": "invalid",
                        "job_id": job_id,
                        "message": f"{job_id} doesn't exist",
                    }
                )
                return

            else:
                if status == "ok":
                    self.write(
                        {
                            "status": "ok",
                            "job_id": job_id,
                            "message": "document ready",
                            "url": f"/documents/{job_id}/document.pdf",
                        }
                    )

                else:
                    self.write(
                        {
                            "status": "pending",
                            "message": "document pending",
                            "job_id": job_id,
                        }
                    )

        else:
            if status == "invalid":
                self.set_status(404)

            self.render('templates/status.html', status=status, job_id=job_id)


class StatusWebSocket(websocket.WebSocketHandler):
    @property
    def pdf_creator(self):
        return self.application.pdf_creator

    async def open(self, job_id):
        job = self.pdf_creator.task(job_id)

        await job

        self.write_message(f"""
                    <turbo-stream action="replace" target="status">
                      <template>
                        <div id="status">
                          <p><a href="/documents/{job_id}/output/document.pdf">Download your PDF</a></p>

                          <p><a href="/">Convert another document</a></p>
                        </div>
                      </template>
                    </turbo-stream>
                    <turbo-stream action="replace" target="header">
                      <template>
                        <h1>Your PDF is ready</h1>
                      </template>
                    </turbo-stream>
                    """)
        self.close(1000)
