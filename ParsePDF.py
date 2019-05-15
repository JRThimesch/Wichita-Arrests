from tika import parser

def getRawText(_file):
    return parser.from_file(_file)

if __name__ == "__main__":
    parsedText = getRawText('05-14-19 Arrest Report.pdf')
    toParse = parsedText['content']
    print(toParse)