## reportgen

reportgen is a python module which acts as a Enginering project calculation explanation document generator. 

It is used to generate an explanation document for engineering calculations being done by any Python module that chooses to use reportgen for generating said explanation

### 20241202-note

moved code over from aeCon

### siva open items 

- [ ] #todo build 20in-report manually from run method
	- [ ] flesh out implementation 
		- [ ] images 
		- [ ] latex expressions 
  - [ ] #todo understand writer.py , method: ReportWriterRegistry, method: register, method: get_writer, do i really need the registry ? can i not just implement? sounds a bit clunky. 
  - [ ] #todo cleanup doris_writers.py 
    - [ ] check - file paths are accurate ?
    - [ ] check - add strict type checking for initialization especially if they are expecting dom (has to DocumentDom)
- [ ] #todo reportgen - move away from using yml to load (and to be implemented) actual report content. switch to a seperate md file.  
- [ ] really understand this whole file path olympics for flush_to_markdown 
- [ ] class : report gen  
	- [ ] #todo understand/refine/implement public edit it (Add/modify/delete)  
	- [ ] #todo understand/refine/implement public print dom contents (to std or yml)  

  - ReportWriter 
		- each implementation is intended to customize the report generation for a specific project or team 
		- each implementation picks whether it wants to write to a docx or a markdown format
		- reportgen-cfg.yml specifies the implementation class to load . 
			- interface or atleast an abstract version of reportwriter validates whether the class mentioned in reportgen-cfg even exists. if not, raises an exception 
			- reportgen initializes this implementation class with the dom ( important paths dictionary )
		- path conversion is done in report writer 
		- "flush" method is left un implemented 

  - DorisMarkdownWriter implements 
		- the flush method 
		- writes md artifact to file 

- DorisDocxWriter implements 
		- the flush method 
		- writes artifact to file 

- [x] refactor reportgen to artifact writer class. 
	- define an interface called ReportWriter. 
		- each implementation is intended to customize the report generation for a specific project or team 
		- each implementation picks whether it wants to write to a docx or a markdown format
		- reportgen-cfg.yml specifies the implementation class to load . 
			- interface or atleast an abstract version of reportwriter validates whether the class mentioned in reportgen-cfg even exists. if not, raises an exception 
			- reportgen initializes this implementation class with the dom ( important paths dictionary )
		- path conversion is done in report writer 
		- "flush" method is left un implemented 
		
	- DocxWriter implements 
		- the flush method 
		- writes artifact to file 

  - MarkdownWriter implements 
		- the flush method 
		- writes artifact to file 

- module : reportgen : run   
	- uses above to generate a report 
	- default implementation will either just load and print loaded report dom to stdout. 
	- if cfg provides artifact version of choice, flushes artifacts of those formats


### assumed user scenarios  

for now lets assume yml is the full persisted dom. (splitting config to yml and report to md makes more sense.. but. for now.. )
- [ ] straight up
```
  directly out of library .i.e. 
  python -m aeUtils exxon-prj1-anal1-cfg.yml
  generates both md and docx reports 
  exxon-prj1-anal1-cfg.yml has
    report details 
    paths - assets,inputs,outputs
    output formats 

```

- [ ] client engagement context - sow/engagement repo : eng models solve the problem , they can also generate portions of the report (could use decorators - I have to figure that out. But the analysis sequence could be not aligned with explanation / report . As In analysis could inverse pyramid but explanation could be a pyramid),  
```
- assignment notes etc  
- analyses  
	- eng models  
	- report generators  
- runs 
	- anal_1 
		- run.sh
		- config.yml
	- anal_2 
- anal_1  
	- assets (report configs and report assets - logos etc)  
	- eng_outputs
	- report_inputs( data, graphs )  
	- reports ( md, docx, yml)

```

### Capabilities 

These are requirements initially outlined for this module. later edits/changes keep preceding.

1. reportgen models a DOM to maintain key attributes of the explanation document. Some of which are  

- explanation details 
  - explanation name : string representing the name of the explanation (e.g.Pipeline Lateral Buckling Evaluation)
  - client logo : png depicting the logo of the client 
  - project name : string representing project name 
  - project num : string representing project date 
  - Engineer : name of engineer 
  - Reviewer : Client representative reviewing this analysis 
  - Date : date the explanation is due. usually static and some date in the near future   
  - target_md_file : clients will set this to specify the file name with which to write the output to markdown. default target_md_file to "default.out.md"
  - project_root :clients will set path to the project root. subsequent important paths will be relative to this project root
  - inputs_path : clients will set path to a folder containing inputs. inputs_path folder can contain images/data etc 
  - assets_path : clients will set path to a folder containing assets that dont change report to report. e.g. client logo etc 
  - outputs_path : clients will set path to a folder where all outputs will be created in this folder. markdown reports or word doc reports , for now.  

- a series of "sections". each section   
  - 1st section is always for report overview level details
  - subsequent sections are added by the users of the module in a sequential fashion 
  - each section has a  
    - unique name ( clients will use this name to retrieve and if needed add to this section) 
    - Title 
    - list of "paragraphs" 
      - each paragraph can have the following 
        - "plain text"  
        - and/or "formatted text"  
        - and/or "text + images"  
        - and/or "latex strings" 
        - and/or "sympy expressions"
      - any component above can appear in any order

1. from a design perspective, follow a singleton pattern for this. 
   - no client has direct access to the data objects in reportgen 
   - all clients will be expected to call a init function to setup the singleton
   - all clients interact with the DOM via access methods above

2. configuraton and input information 

3. reportgen provides capabilities that make it easy for client-code to add content for the explanation DOM 
  - add a new section to the dom
  - tracks "current" section to which contents are being added
  - switch to a section specified (from current section)  by the client. if the section name provided by the client does not exist, it creates a new section with this name, assigns the name as the title. 
  - provides a function that make it easy for clients to "edit" the current section, to
    - change the title of section
    - append paragraph, taking in an input string  
    - append paragraph, taking in an input string and an optional sympy.expression type. this apppends 2 paragraphs. 
      - first is the input string 
      - second paragraph is the latex version of the sympy expression (i.e. sympy.latex(expression_parameter))
    - supports sympy.expressions. has a function to accept 
  - provides a decorator (lets call this "explain_function"), which when added before a function in client code (lets call this client-function),
   - decorator has an optional text parameter that accepts a "client-function purpose"
   - prints the recieved "client-function purpose" text to a new paragraph in current section of dom 
   - inspects inputs to client-function
   - appends a text version of input parameter names and parameter values to the current section of dom as a new paragraph 
   - inspects output of client-function 
   - appends a text version of output parameter name and parameter value to the current section of dom as a new paragraph

4. reportgen provides a function that converts the data in the dom into a markdown document (lets call this flush_markdown)
   - write markdown output to target_md_file 
   - ensure no open file descriptors or handles after flush is executed. 

5. reportgen provides a function that converts the data in the dom into a word document (lets call this flush_docx)
   - write microsoft word compatible output to target_docx_file 
   - ensure no open file descriptors or handles after flush is executed. 

6. persist dom as config.yml - reportgen provides a function that allows users to persist the current dom (contents and the structure) into a yml file. this yml will follow conventions for aeUtils config.yml (basename is mandatory. remaining structure and contents specific to each module)

7. load dom from config.yml - report provides a function that allows users to "load" a dom (contents and structure) from a yml file. the yml file is expected to adhere to aeUtils config.yml conventions. 


4. reportgen supports sympy.expressions 

