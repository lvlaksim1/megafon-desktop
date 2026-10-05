from megafon_desktop.megafon.browser_transport import BrowserCaptureTransport, ResponseCapture


def test_response_capture_keeps_only_known_successful_json():
    capture = ResponseCapture()
    assert capture.observe("https://lk.megafon.ru/balance/api/main", 200, {"balance": 12})
    assert not capture.observe("https://lk.megafon.ru/unknown", 200, {"x": 1})
    assert not capture.observe("https://lk.megafon.ru/balance/api/main", 500, {"balance": 0})
    assert capture.latest("balance/api/main") == {"balance": 12}


def test_payload_value_supports_wrapped_data():
    assert BrowserCaptureTransport._payload_value({"balance": 1}, "balance") == 1
    assert BrowserCaptureTransport._payload_value({"data": {"balance": 2}}, "balance") == 2
    assert BrowserCaptureTransport._payload_value({}, "balance") is None
