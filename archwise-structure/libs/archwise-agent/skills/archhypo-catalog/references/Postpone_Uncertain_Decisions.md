# Postpone Uncertain Decisions

## AKA Finding Responsible Moments

Architectural decisions can affect the whole software meaningfully and potentially generate a significant amount of rework in case of a change. For that reason, many teams adopt an upfront approach to the architecture, making decisions at the beginning of the project. However, there might be uncertainties regarding the requirements and solutions that do not favor making these decisions at that moment. One of the principles of Continuous Architecture advises postponing architectural decisions. However, there is not much guidance on how that can be done safely and how a responsible moment can be identified to make that decision.

**How to create a plan to postpone architectural decisions safely, leaving them to a responsible moment?**

- In several projects, the software architecture design is done at the beginning of the project.
- Changes in architectural decisions can have a high impact on software.
- At the beginning of the project, there is a lack of important information for making architectural decisions.
- Continuous Architecture principles advise postponing architectural decisions to the most responsible moment.

Therefore:

**Identify the hypothesis affecting a target architectural decision and plan actions to reduce their uncertainty and impact. Use the outcome of these actions to identify a responsible moment for making the decision.**

Making an important architectural decision when the team does not have all the information can be dangerous. So, before deciding, the team should consider the hypothesis that can influence that decision. When uncertainties are related to that decision, it is a good reason to postpone and plan or manage actions to reduce the uncertainties. When postponing a decision, the impact of making that decision should be considered.

A simple temporary solution can be adopted when something in the software is necessary to continue the software development activities. For example, if the decision is related to a validation component to be adopted, a simple one can be used until a decision is made. In this case, techniques to reduce the impact of changing it in the future, such as creating a Facade to isolate it, should be considered. When reducing that impact is not possible or viable, the team should act on reducing the uncertainty to make that decision as fast as possible.

Temporary solutions can easily become permanent, and that is not a problem if, in the end, they fulfill the application requirements. However, if the uncertainty remains, even if the adoption of this solution reduces the impact, the associated hypothesis should keep being managed by the team. This way, even if the current solution is considered temporary, it will not be forgotten, and the consequences of having it there will still be managed.

When a decision is postponed because of the high uncertainty involved, the team should also perform actions that gather more information about it. As a result of each of these actions, the uncertainty will be reduced, providing more knowledge for the team to make that decision.

According to the patterns **Uncertainty Level** and **Hypothesis Impact**, after performing actions that can affect a hypothesis, the impact and uncertainty should be reassessed. When a hypothesis is considered resolved, in other words, there is no more uncertainty, the decision associated with it is ready to be made. It is recommended to have at least a low uncertainty to move forward. Hypotheses evaluated with a low impact are good candidates to be postponed until the uncertainty is solved or it is really needed. Ultimately, the team has autonomy to choose when is a responsible moment for a given decision, and the information about the hypotheses can be used to support that.

Some patterns, like **Architectural Trigger** and **Agile Landing Zones**, can also be applied to determine the criteria for when some additional action should be taken. In this case, it can be used as a way to monitor an uncertainty aspect and use it to determine when it is time to take action.

## Examples

_Consider that the team is uncertain if the system will fulfill the current requirement on response time, and write a hypothesis that captures it. Since the system load and the impact on the performance of some solutions are unknown, the decision was postponed. To reduce impact, all access to components that can harm the performance was isolated and the layers were designed in a way that would make it easy to cache external calls._

_In the same example, to have information on the current state of the system, a response time measurement was added in production. The team decided that it was enough for now, but defined an Architectural Trigger if the response time gets close to the requirement to proceed with further actions._

_In the Catch Solve project, an issue related to architecture was raised, specifically regarding a potential problem with the availability of the application. The presented hypothesis expressed concerns about the lack of redundancy, potentially impacting the application's availability for customers. Initially, the team considered this hypothesis to have very low uncertainty level and impact, given that the Catch Solve application is not a critical solution for their customers, and the team identified the problem as quickly resolved. Nevertheless, a primary action plan was devised to monitor application availability through unavailability reports, and an Architectural Trigger based on the number of new customers was incorporated to revisit the issue. After this action, the Startup had the confidence to postpone the decision to introduce redundancy in its runtime environment._

_In the Kardashev project, the team grappled with a crucial hypothesis in the core development phase: the incomplete integration of game systems within the Entity Component System (ECS) framework. ECS, a programming paradigm in game development, separates concerns by dividing objects into entities, components, and systems, which enhances efficiency and performance. The high impact of this hypothesis stemmed from the potential for improved game performance and system compatibility. To address the uncertainty and ensure a smooth transition, a performance testing suite was established. Integrated into the Continuous Integration and Continuous Delivery/Deployment (CI/CD) pipeline, it rigorously tests system performance and compatibility after each update, focusing on optimizing integration within the ECS framework. This strategy effectively manages the risk associated with ECS integration, ensuring that game development progresses with an emphasis on system compatibility and performance enhancement._

## Consequences

The following are the consequences of using this pattern:

- The team has an uncertainty and impact assessment to plan for the right time to make architectural decisions that depend on uncertain factors.
- It is possible to anticipate possible impacts and work on solutions that minimize them.
- When an architectural decision is delayed, the team has more time to gather the information needed to make a more informed decision.
- Sometimes, to initiate a project, there are decisions with a high impact that cannot be postponed.
- Even taking action to minimize the impact, delaying a decision can generate more work than if the decision was made earlier.

## Related Patterns

This pattern relates directly with **Architectural Hypotheses**, **Uncertainty Level** and **Hypotheses Impact** to postpone decisions. **Architectural Trigger** and **Agile Landing Zones** can be used to define criteria on when additional actions should be taken by the team.
