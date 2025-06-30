import logging
import os
import warnings
from typing import Optional

import requests

__all__ = ["RPCException", "Aria2Client", "MulticallClient"]

logger = logging.getLogger(os.path.basename(__file__))


class RPCException(Exception):
    def __init__(self, code, msg):
        self.code = code
        self.msg = f"[{code}] {msg}"

    def __str__(self):
        return self.msg


class Aria2Client:
    """
    jsonrpc client for aria2
    """

    def __init__(self, host: str = "localhost", port: int = 6800, token: Optional[str] = None, session=None):
        """
        @param host: Aria2 rpc host
        @param port: rpc port
        @param token: rpc authentication token
        """
        if session is None:
            session = requests.Session()
        self.session = session
        self.host = host
        self.port = port
        self.token = token

    def __del__(self):
        self.session.close()

    @property
    def server(self):
        return f"http://{self.host}:{self.port}/jsonrpc"

    @property
    def ws_server(self):
        return f"ws://{self.host}:{self.port}/jsonrpc"

    @staticmethod
    def check_resp(response: dict):
        if "error" in response:
            logger.error(response)
            raise RPCException(response["error"]["code"], response["error"]["message"])
        return response["result"]

    def call(self, method: str, params: Optional[list] = None):
        """
        Call a rpc method
        @param method: method name
        @param params: method parameters
        @return: call result
        """
        payload = self.get_payload(method, params)
        logger.debug("Calling rpc method: {method}({params})".format(method=method, params=params))
        response = self.session.post(self.server, json=payload).json()
        return self.check_resp(response)

    def get_payload(self, method: str, params: Optional[list] = None) -> dict:
        if params is None:
            params = []
        if self.token and method.startswith("aria2."):
            params.insert(0, f"token:{self.token}")

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "id": 0
        }
        if params:
            payload["params"] = params
        return payload

    def add_uri(self, uris: list, options: Optional[dict] = None):
        if options is None:
            options = {}
        return self.call("aria2.addUri", [uris, options])

    def pause(self, gid: str):
        return self.call("aria2.pause", [gid])

    def pause_all(self):
        return self.call("aria2.pauseAll")

    def unpause(self, gid: str):
        return self.call("aria2.unpause", [gid])

    def unpause_all(self):
        return self.call("aria2.unpauseAll")

    def remove(self, gid: str):
        return self.call("aria2.remove", [gid])

    def get_option(self, gid: str) -> dict:
        return self.call("aria2.getOption", [gid])

    def get_uris(self, gid: str) -> list[dict]:
        return self.call("aria2.getUris", [gid])

    def tell_status(self, gid: str, keys: Optional[list] = None) -> dict:
        if keys is None:
            keys = []
        return self.call("aria2.tellStatus", [gid, keys])

    def tell_active(self, keys: Optional[list] = None) -> list[dict]:
        if keys is None:
            keys = []
        return self.call("aria2.tellActive", [keys])

    def tell_waiting(self, offset: int, num: int, keys: Optional[list] = None) -> list[dict]:
        if keys is None:
            keys = []
        return self.call("aria2.tellWaiting", [offset, num, keys])

    def tell_stopped(self, offset: int, num: int, keys: Optional[list] = None) -> list[dict]:
        if keys is None:
            keys = []
        return self.call("aria2.tellStopped", [offset, num, keys])

    def purge_download_result(self):
        return self.call("aria2.purgeDownloadResult")

    def remove_download_result(self, gid: str):
        return self.call("aria2.removeDownloadResult", [gid])

    def shutdown(self):
        return self.call("aria2.shutdown")

    def get_global_stat(self):
        return self.call("aria2.getGlobalStat")

    def get_version(self):
        return self.call("aria2.getVersion")

    def restart_download(self, gid: str) -> str:
        status = self.tell_status(gid)
        if status["status"] != "error":
            warnings.warn("Only failed tasks can be restarted")
            return gid

        option = self.get_option(gid)
        uri = status["files"][0]["uris"][0]["uri"]
        new_gid = self.add_uri([uri], option)
        self.remove_download_result(gid)
        return new_gid

    def retry_all(self):
        stopped = self.tell_stopped(0, 9999)
        for task in stopped:
            if task["status"] != "error":
                continue
            self.restart_download(task["gid"])

    def get_all_downloads(self) -> list[dict]:
        return self.tell_active() + self.tell_waiting(0, 9999) + self.tell_stopped(0, 9999)


class MulticallClient(Aria2Client):
    """
    Multicall client
    """

    def __init__(self, parent: Aria2Client):
        super().__init__(host=parent.host, port=parent.port, token=parent.token, session=parent.session)
        self.call_list = []

    def call(self, method: str, params: Optional[list] = None):
        """
        @param method: RPC method name
        @param params: method params
        @return: Payload that will be added to the call list
        """
        payload = self.get_payload(method, params)
        self.call_list.append(payload)
        return payload

    def multicall(self) -> list:
        """
        Call multiple methods in the call list
        @return: a list of call results (if success)
        """
        response = self.session.post(self.server, json=self.call_list).json()
        self.call_list = []
        results = []
        for r in response:
            results.append(self.check_resp(r))
        return results

    def restart_download(self, gid: str):
        raise NotImplementedError
