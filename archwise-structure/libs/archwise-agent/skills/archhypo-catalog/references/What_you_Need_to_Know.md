# What You Need to Know

## AKA Focus on Key Issues, Highlight Your Questions, What You Want to Improve

Development teams know that metrics and other kinds of information can be extracted from their systems to support decision-making. Development activities generate a large amount of data. Various software artifacts including source code, bug reports, commit history, test executions, etc. could provide valuable insights about software projects. Several tools can extract such data from the development environment at runtime. Although teams are aware of the existence of software data to be explored, they often do not know where to start to leverage it in their software improvement activities.

**How can we employ software analytics to improve the software aspects and/or our development process?**

- Software practitioners produce different data-rich software artifacts, but they usually do not use the data to support their decisions.
- Many tools were developed to support the software analytics deployment, but most of them can be time-consuming to install and configure.
- For many development teams, it may be difficult to start a software analytics project because of lack of time, but they need to consider their benefits for software improvement.
- Some tools can generate a huge amount of data by default from the development environment at runtime, but the team should just focus on the data that will be useful to solve a given issue.

Therefore:

**Define the key issues that the development team wants to focus on, to improve the software throughout the project.**

During the development of the product, issues around software aspects arise to be solved. The team frequently makes decisions to solve them based on experiences and intuitions. However, the team may not have enough information to solve a given issue. Such an issue can be related to the structure of the source code, the development process, or the business rules. By defining the key issues that need to be addressed, the team can focus on efforts to solve them through a data-driven investigation to obtain meaningful information to support any decisions. Some decisions might lead to one-time action, for instance, when the team needs to prioritize the implementation of an architectural component to improve the system's performance. Or it might be a series of continuous decisions and actions that need to be performed through the iterations, such as for what part of the system we need to prioritize refactoring. A guiding question at this stage could be "What should we measure now?"

## Examples

_As an example, imagine that a development team wants to improve their tests and needs to decide where in the system they should put their effort. Using What You Need to Know, a possible question highlighted by the development team might be "What data is required to verify software test adequacy?". By answering this question, the team can avoid unnecessary data gathering, and plan better on how to collect useful data to investigate the issue._

## Consequences

As a consequence, the team will understand the reason behind the data being collected, making better use of them. Additionally, unnecessary data will not be collected and will not take away the focus of the team on what is more important. Sometimes, tools can detect unexpected problems based on measurements that do not have a known reason. Focusing only on a subset of that information, the team can fail to notice a potential problem.

## Examples from Literature

_Jian-Guang Lou et al. formulated questions about incident-management as a software-analytics problem. For them, incident management of an online service requires the service provider to take action immediately to resolve the incident, since the cost of each hour's service downtime is high. As the use of debuggers to conduct diagnosis on services is usually impracticable, the teams need to highlight other questions to detect anomalies and quality issues at runtime of the service._

_Robert L. Nord et al. presented a series of questions related to measurement and analysis for software architecture and about how to meet the business goals of software. According to them, there is an increasing need to provide ongoing insight into the quality of the system being developed. Thus, the team's questions might be, for instance, about how to improve feedback between development and deployment through means to measure intrinsic quality, value, and cost. In the case presented by Gregorio Robles et al., the information about the development effort invested in a project was considered a business strategy. And, the question highlighted by the development team was related to how to obtain software development estimations with a bounded margin of error._

## Related Patterns

The pattern Find Essential Qualities focused on quality assurance is linked to this pattern. Since software analytics is not just addressed to solve quality issues, our pattern also encompasses other software aspects, from the development process to business requirements. As an example of supporting strategic and tactical decisions, an issue to solve could be the need for a reduction in the overwork of developers. After defining What You Need to Know, in the next step, the team needs to Choose the Means to solve the related issue.
