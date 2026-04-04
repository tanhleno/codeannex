from pygments.token import Token

TOKEN_COLORS = {
    Token:                   "#cdd6f4",
    Token.Keyword:           "#cba6f7",
    Token.Keyword.Namespace: "#89dceb",
    Token.Name.Function:     "#89b4fa",
    Token.Name.Class:        "#f9e2af",
    Token.Literal.String:    "#a6e3a1",
    Token.Literal.Number:    "#fab387",
    Token.Comment:           "#6c7086",
    Token.Operator:          "#89dceb",
}


def get_token_color(ttype) -> str:
    while ttype is not None:
        if ttype in TOKEN_COLORS:
            return TOKEN_COLORS[ttype]
        ttype = ttype.parent
    return "#cdd6f4"
