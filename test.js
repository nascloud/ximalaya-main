<html>
    <head>
        <script src="https://s1.xmcdn.com/yx/static-source/last/dist/js/dws1.7.4.js"></script>

        <script type="text/javascript">

            var n = "t6pfoml9679z52kqw93uqu75eflqdg1bykhl", o = "h5_goyxvzyohd", a = "";

            var dwsGetBrowserId = function() {
      if (window.du_web_sdk)
            return a ? Promise.resolve(a) : new Promise((function(e, t) {
                window.du_web_sdk.getBrowserID(n, o, "", (function (t) {
                    t && (a = t),
                        e(t || "")
                }
                ))
            }
            ));
            return Promise.resolve(a)
  }

            var dwsGetSessionID = function() {
      if (window.du_web_sdk)
            return new Promise((function(e, t) {
                window.du_web_sdk.getSessionID(n, o, "", (function (t) {
                    e(t || "")
                }
                ))
            }
            ));
            return Promise.resolve("")
  }

            function displayBrowserAndSessionId() {
                Promise.all([dwsGetBrowserId(), dwsGetSessionID()]).then(function (results) {
                    document.getElementById('output').innerText = `${results[0]}&&${results[1]}`;
                }).catch(function (error) {
                    document.getElementById('output').innerText = 'Error: ' + error;
                });
        }

        </script>
    </head>

    <body>

        <button onclick="displayBrowserAndSessionId()">test</button>
        <div id="output"></div>
</html>