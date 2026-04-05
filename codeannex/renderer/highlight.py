from pygments.token import (
    Token, Comment, Keyword, Name, String, Number, Operator, Punctuation, Error
)

TOKEN_COLORS = {
    Token.Text: "#cdd6f4",
    Comment: "#6c7086",
    Keyword: "#cba6f7",
    Name: "#89b4fa",
    Name.Function: "#89b4fa",
    Name.Class: "#f9e2af",
    String: "#a6e3a1",
    Number: "#fab387",
    Operator: "#89dceb",
    Punctuation: "#94e2d5",
    Error: "#f38ba8",
}

def get_token_color(ttype):
    while ttype not in TOKEN_COLORS and ttype.parent:
        ttype = ttype.parent
    return TOKEN_COLORS.get(ttype, "#cdd6f4")
