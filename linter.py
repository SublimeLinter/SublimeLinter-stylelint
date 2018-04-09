import json
import re

from SublimeLinter.lint import NodeLinter


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

        We override this method to handle parsing stylelint crashes.
        """
        data = None
        match = self.crash_regex.match(output)

        if match:
            msg = "Stylelint crashed: %s" % match.group(1)
            yield (match, 0, None, "Error", "", msg, None)

        try:
            if output and not match:
                data = json.loads(output)[0]
        except Exception:
            yield (match, 0, None, "Error", "", "Output json data error", None)

        if data and 'invalidOptionWarnings' in data:
            for option in data['invalidOptionWarnings']:
                text = option['text']

                yield (True, 0, None, "Error", "", text, None)

        if data and 'deprecations' in data:
            for option in data['deprecations']:
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
