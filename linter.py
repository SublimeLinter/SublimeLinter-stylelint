import json
import re
import logging
from SublimeLinter.lint import NodeLinter

logger = logging.getLogger('SublimeLinter.plugin.stylelint')


class Stylelint(NodeLinter):

    npm_name = 'stylelint'
    cmd = 'stylelint --formatter json --stdin --stdin-filename ${file}'

    line_col_base = (1, 1)

    crash_regex = re.compile(
        r'^.*?\r?\n?\w*Error: (.*)',
        re.MULTILINE
    )

    defaults = {
        'selector': 'source.css - meta.attribute-with-value, source.less, source.sass, source.scss'  # noqa 501
    }

    def find_errors(self, output):
        """
        Parse errors from linter's output.

        We override this method to handle parsing stylelint crashes,
        deprecations and other feedback about the config.
        """
        data = None
        match = self.crash_regex.match(output)

        if match:
            msg = "Stylelint crashed: %s" % match.group(1)
            self.notify_failure()
            yield (match, 0, None, "", "Warning", msg, None)

        try:
            if output and not match:
                data = json.loads(output)[0]
        except Exception:
            self.notify_failure()

        if data and 'invalidOptionWarnings' in data:
            for option in data['invalidOptionWarnings']:
                self.notify_failure()
                text = option['text']
                yield (True, 0, None, "", "Warning", text, None)

        if data and 'deprecations' in data:
            for option in data['deprecations']:
                self.notify_failure()
                text = option['text']
                yield (True, 0, None, "", "Warning", text, None)

        if data and 'warnings' in data:
            for warning in data['warnings']:
                line = warning['line'] - self.line_col_base[0]
                col = warning['column'] - self.line_col_base[1]
                type = warning['severity']
                text = warning['text']

                if type == 'warning':
                    yield (True, line, col, "", type, text, None)
                else:
                    yield (True, line, col, type, "", text, None)

        return super().find_errors(output)
