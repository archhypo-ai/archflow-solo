# Learning from Experiments

## AKA Run Experiments, Measure with Experiments

The issues that emerge in software analytics can be related to different needs. At the development process level, the team may need to evaluate for instance new methods, tools, or practices. At the product level, the team may need to evaluate the requirements, features, or usage data. At the user experience level, they may need to evaluate product usability, user satisfaction, design aspects, etc. Some of these issues can be investigated through data collected from the development environment and software artifacts such as source code, bug reports, test cases, usage logs, documentation, etc. For other issues, however, the team may need to evaluate the usability of a feature that has not yet been implemented. Even further, the team may have implemented a feature that needs to be improved but does not know how to improve it. In both these situations, the team has nowhere yet to collect and analyze data to support their decisions.

**How can we obtain information to make informed decisions about software issues on some aspect we have not yet implemented or we need to redesign?**

- The team often has more than one way of implementing the same feature, using different methods and tools for development, and adopting different alternatives of architectural design, but they need to seek to make their choices as successful as possible.
- Sometimes the team makes a decision that will be simple to reverse if it does not work out, but some solutions are worth experimenting with before implementation to avoid wasting resources and rework.
- Experiments can fail, but the team can improve the experiment design by analyzing what went wrong.
- Sometimes, experiments can produce inconsistent results, but the team can investigate the cause of such inconsistencies and then conduct new experiments if they prove feasible.

Therefore:

**Create an alternative solution and perform an experiment collecting data that allows the comparison with the current solution.**

Experiments allow us to test our hypotheses for better decision-making. Results from experiments can provide us with relevant information to find the best alternatives for design, tools, approaches to development, and test methods, among others. Through experiments, we can compare two different approaches, where the control group can be an existing solution in use. That is, we can verify whether an idea is promising or if it makes no sense to continue with it. At this stage, a guiding question could be "How should we test our ideas?" Experiments can have a low cost of implementation. However, before opting for experimentation, the team always needs to weigh the cost of doing one or more experiments with the cost of re-engineering or redesigning after you implement something. The team needs to have a clear purpose for the experiment and have a reasonable hypothesis to test. The experimental design should be carefully planned, and the experimenters should know which aspects of the software or process will be observed.

During the experimental design planning, the team should be especially careful also to define the experiment size, as large experiments can be costly and unfeasible. Both ROI and the time to implement an experiment are important factors to be considered by the team before adopting them. Sometimes experiments may not work out, and sometimes they can produce conflicting or unclear results. When an experiment does not provide useful information or has unclear results, the team decides if new experiments should be carried out from the lessons learned. Replicating an experiment may be impractical depending on its cost and size. Small experiments tend to be cheaper and easier to replicate. About experimenting and learning, worth taking into consideration Linda Rising's advice:

> "You can't realistically plan anything from the beginning; the only way to reach your long-term goals or solve your big problems is to try a small thing and learn from the experience. That's how we have always learned. Babies do this from the start. It's the basis for the scientific approach. Experiment and learn."

## Examples

_As an example, imagine that a development team wants to increase the number of hits/clicks on related products in an e-commerce application. Currently, in this application, the products are merely recommended according to the category. The team has the following idea: an algorithm to recommend products that were recently bought with the product being searched. Additionally, the team wants to rearrange products on the user interface. They do not know how much it will be pleasing to the end-user. To save time and effort, the team develops some prototypes and runs an experiment with a limited number of users, representing the target audience. From the experiment results, they were able to know which was the best option for the user interface redesign._

## Consequences

As a consequence, the results of experimentation can produce insightful information about the product or the development process, that is, the reliable and valuable knowledge needed to make better decisions.

- Sometimes, team members can be biased in how they interpret the results of an experiment. If it doesn't produce the results they expect, they may discount the results or find ways to invalidate the experiment.
- Other times, the results of an experiment may be inconclusive. In that case, the team must decide whether to perform another experiment to pick among equally viable options.
- An experiment can also provide misleading information which did not test the hypothesis. In that case, the team may have to spend time figuring out why something you thought would improve the system did not.

## Examples from Literature

_Kim et al. investigated the competencies and working styles of data scientists in software-oriented data analytics context. They reported an increase in the randomized two-variant experiments called A/B testing to assess the requirements and utility of new software features. Because of numerous possibilities for alternative software designs, data scientists along with engineering teams have built software systems to inject the changes, called flighting._

_Gousios et al. introduced the concept of streaming software analytics and proposed a data analytics infrastructure that unifies the representation of historical and current data as streams and enables high-level aggregation and summarization using a common query. This approach can facilitate the execution of experiments, as well as data collection and correlation of the results of applying specific design and development decisions and their outcomes._

_Liechti et al. introduced the idea of test analytics to help an agile development team improve their test process. Focusing on collaborative practices, they organized a series of workshops to train the team and started with small experiments on simple features which allowed them to evaluate and select a set of tools and to create a collection of examples._

## Related Patterns

Build Prototypes is a related pattern that highlights the usefulness of prototypes in experiments to understand requirements, validate requirements with customers, explore human/computer interactions for the system, or explore the cost and benefits of design decisions. Early Validations is another pattern addressed for software startups. In that pattern, experiments are performed to validate or reject an initial hypothesis and make decisions about the direction of the project based on acquired knowledge. Learning from Experiments is a way to test ideas and possible solutions in response to What You Need to Know.
