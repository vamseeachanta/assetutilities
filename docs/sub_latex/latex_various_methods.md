
## Markdown in Github

<https://github.blog/news-insights/product-news/math-support-in-markdown/>

<https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/writing-mathematical-expressions>

References:

<https://mathpix.com/docs/mathpix-markdown/syntax-reference>

## Latex from Python

<https://tex.stackexchange.com/questions/885/how-can-i-use-latex-from-python>

Hand calcs:
<https://github.com/connorferster/handcalcs#basic-demo>

latexify_py:

### Pandoc and Latex

<https://miktex.org/download>

<https://github.com/jgm/pandoc/releases/tag/3.3>

## PDFLATEX

Packages required:
pdflatex
pythontex

<https://www.12000.org/my_notes/python_in_latex/index.htm>

## Rendering Mathematics Equations (MathTex, MML, Latex)

<https://markdownmonster.west-wind.com/docs/_59l0mv2uw.htm>

## Handcalcs - Reddit comments

<https://www.reddit.com/r/Python/comments/ijjppe/i_created_a_library_called_handcalcs_it_renders/?rdt=41236>
https://www.kaggle.com/code/ahmettezcantekin/handcalcs-python-calculations


I really like this, coincidentally I saw it on PythonBytes episode #192 today before I saw this post. I HATE HATE HATE using excel for engineering calculations. I used MathCAD when I had access to it, but have been waiting for something in the open source arena that compared. Jupyter notebook has made it easier but I still find I have to essentially write my equations twice, once in LaTEX/markup and once in the command line in order for it to be clear what is going on and it may be my python ignorance, but I'm not proficient with sympy <-> numpy to get results and graph things easily or explore equation relationships.

One thing that I would love to see with this is if it integrated nicely with "pint" for units, which imo the best units package. I just tried it out and all of the outputs are surrounded by $ symbols, e.g. $3 meters$, which makes it look a little clunky. I haven't delved very deep into it at all, so there may be something I'm missing by reading the documentation. Units and unit conversions are ESSENTIAL for making this be an effective engineering tool.

This is nice! Some tips though, coming from someone who writes tons of latex:

We don't use so many \cdot. Only when there's ambiguity, such as multiplication between two numbers. You don't need them between numbers and letters, or between letters.

In a similar vein, you often have too many parentheses (as in your video with the quadratic formula), or not enough (I could get it to write -1·-1).

Rendering underscores as subscripts is cute but we don't use underscores that way in Python. I think subscripts is more akin to indexing expressions, so a[i] ? a_i.

x = ab is rendered as a multiplication between a and b, not as a single variable whose name is "ab".

I get a KeyError when rendering a pure expression (no assignment).

Generally, single letter names should be in italics and multi-letter names should be in upright text. That also goes for functions!

Edit:

It gets the value of 1e-2 right (0.01) but the symbolic expression reads as one times e minus two. I don't know how you render units but the siunitx package parses expressions like this wonderfully, so if you're already using it you can probably wrap all number literals in it.
