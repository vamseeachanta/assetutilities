https://www.linkedin.com/posts/gunnar-andreas-staff-a19400_cognite-atlas-ai-activity-7289761598892642304-zejN?utm_source=share&utm_medium=member_desktop

A question many engineers ask themselves today is: what can an Industrial Agent do for me?

While generative AI like GPT, Gemini, and Claude are useful for general information, they rarely address specific industrial challenges due to the risk of inaccurate or even dangerous recommendations.
Why is that? Because we do not know where the answer came from. The well established solution to this is RAG, meaning that instead of asking the LLM for the answer we ask it to find it in our data. But can we do better? Yes we can, by using Context Augmented Generation where we tell the LLM to look inside a semantic Industrial Knowledge Graph. Now we do not need to search for the right document in a pool of millions of documents, but instead find the equipment in question and then pull the contextualised spec doc.

So far so good; we can now find the data faster, however, we still need to analyse it. But can the LLMs do math? Not really, but they can call a ?friend? that does it for them. Eg, when you ask what is the correlation between two timeseries it can call upon its friend scipy, executing scipy.signal.correlate. Like your general practitioner cannot do everything him/herself, but instead ask the nurse to draw blood and the lab worker to analyse it, the LLM is also using external expertise to perform complex tasks. It doesn?t need to know how, but instead what you want to do and who is able to do it, and then ?delegate?. 
What if I have a very complex analysis? Implement the function and/or connect to your favourite simulator, and make sure that the purpose of the method and input/output is well documented, and available via an API. Easy-peasy? For most engineers, not anymore. 

This is where Atlas AI comes in, bringing all the building blocks together, allowing you to quickly configure your own agents.
It gives you the knowledge graph, is allows you to write your own calculation routines and ?upload? them such that all this mysterious API requirements are created automagically, it provides the simulator connectors such that a simulation can be made available (and understandable) to the LLM, and it connects all of this via a user interface that a normal human can comprehend. 

Suddenly we have agents that not only find the data, but also perform complex analytics. 
?What will the consequence on the production be if I change the operating pressure to X??
?If I shut down my gas-condensate pipeline now, when will it start to form hydrates??. 

Do you need Atlas AI to perform this? Of course not. If you want to you can manually search for the sensor readings in your historian, download it or set up the live connector, implement your analytics in python and/or push the operational settings into your simulator model and configure the what-if/optimisation scenarios, and then extract the results and interpret/plot them. 
If you do not want to go through all that pain you should consider checking out Atlas AI