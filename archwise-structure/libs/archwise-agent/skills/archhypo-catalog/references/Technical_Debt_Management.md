# Technical Debt Management

Technical debt can accumulate, if you don't take time to rework and improve the design of your system. Technical debt is not a simple issue. The cost of accruing significant technical debt makes it more difficult to rapidly change and evolve your system. Fixing designs problems is often more costly the longer you delay. A recent study revealed that the management of existing debt can help avoid its uncontrolled growth.

Accruing some technical debt can be prudent and even desirable. One needs to balance the cost of making any design improvement with implementing new functionality. You may consciously decide to take on technical debt in order to learn something about your system and its use before improving your design. However, inconsistencies and inadequate design choices can become overwhelming if not addressed. Technical debt can compound over time if it is not managed.

**How can you protect your architecture from the ravages of uncontrolled technical debt?**

Some debt happens unintentionally through misunderstanding or errors in judgment. Technical debt is inevitable on any project. There isn't enough time to always improve functionality that "works well enough." On the other hand, if you do not work towards a **Sustainable Architecture**, technical debt can grow and cause your system to devolve in a poorly architected **Big Ball of Mud**.

It is often hard to know what appropriate action to take to reduce some technical debt. The long term consequences of a particular design choice and its accumulated effects on the overall system can be hard to understand. Deferring design rework until after you have learned more can have a huge payoff. Some debt is urgent and easy to fix. Some debt may be costly and hard to fix. Some debt may be easy to remedy but isn't that significant. Prioritizing debt reduction efforts can be difficult.

Some technical debt does not cause problems as it is in a part of the system which is fairly stable and isn't changing much. Trying to pay off that debt may be more costly than any benefit that comes from reducing it. However, the economics may change in the future, when that part of the system needs significant enhancements. Subsequently, it can become worthwhile to pay off the debt.

Some short term debt can be good for tactical reasons. It may be more valuable to release the software and get feedback on new features rather than clean up some existing technical debt. Sometimes long term debt can be taken on proactively for business reasons.

Therefore:

**Identify and manage the technical debt present in the project along with the respective effort to fix it.**

To manage technical debt, consider the effort to fix it, the consequences that debt has on the current users of the system and ongoing development, and how much that debt is projected to compound if not fixed. **Technical Debt Management** takes time and requires discipline from the team. However, reducing debt need not consume all of a team's energies. The most critical problems should be prioritized first. Not all debt is equally important to reduce. For example, it may be more critical to fix a performance issue that is slowing down every user than to re-implement a service in order to use the standard logging mechanism.

The amount of technical debt and architecture work can be made apparent by coloring backlog items to make them stand out: architecture features including quality-related items can be colored yellow and technical debt reduction items colored black.

If the technical debt is extensive it can be difficult to balance debt reduction with new feature development. Sometimes a product owner may not want debt reduction items on the main product backlog because their main focus is on delivery of new features. In that case, create a separate technical debt reduction backlog which is prioritized separately. One issue to resolve when having separate backlogs is how to coordinate the work and manage dependencies between User Stories and debt reduction tasks. While some believe there should be only one backlog, there can be benefits to having a separate technical backlog. A separate team might be dedicated to reducing technical debt while addressing architecture tasks. Do what works best to keep the proper focus and priorities clear.

Technical debt reduction efforts need monitoring and metrics can be gathered by using existing code analysis tools. **Continuous Inspection** can be used to examine debt and monitor its impact. Inspection tools can be used to verify how much the debt is growing. There are different approaches for reducing technical debt. Refactoring the system to eliminate the debt is the most straightforward approach. However, depending on scope of the refactoring effort, it can require a lot of investment that might not pay off.

Another option for containing debt instead of reducing it, is to isolate debt ridden parts of a system to minimize their impact on the rest of the system by applying patterns such as **Sweeping it Under the Rug**, **Wiping Your Feet at The Door** and **Anti-Corruption Layer**.

When the team does not know how to address some specific technical debt, it can use an **Architectural Spike** to explore possible solutions. An **Architectural Trigger** can be used to identify when technical debt has become a problem that needs to be handled.

## Examples

*Pires et. al conducted a study of three teams at a large company which revealed that visibility of problems and their consequences was increased by managing technical debt.*

*Noman found that reducing clutter in code by making simple refactorings first, makes it easier to make more architecturally significant refactorings. He also found that if debt reduction occupies more than 10% of their overall workload, teams become weary of debt reduction and that the amount of time a team spends on debt reduction has diminishing returns.*

*The Refactory collaborated with a development team that scheduled 1 out of every 4 sprints dedicated to technical debt management. This was an agreement between their customer and the development team. They did not always use the sprint for technical debt management but had it in the plan if needed.*
