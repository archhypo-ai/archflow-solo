# Protective Guideline

## AKA Programming for Future Decisions, Open Architecture Guideline

When a system is being developed, some programming practices might limit or affect some decisions that can be used in the future. For instance, relying on centralized variables, like static ones, to share information among classes can make it harder to distribute and parallelize the software components. Programming practices might also affect other quality attributes, such as security, performance, and testability. When there are some uncertainties related to the software architecture, even if some requirements and solutions are still unknown, it is not desirable to limit future options. However, the development team might unconsciously do something that can affect future choices.

**How to prevent developers from adopting solutions and practices that might limit future architectural decisions?**

- The adoption of certain programming practices can profoundly impact both current operations and future flexibility.
- When a development team commits to specific architectural and design choices, they may inadvertently limit their options for future changes.
- Solutions in the code focused on immediate problems can result in significant challenges for future modifications.
- There are programming practices, such as modularity techniques and usage of metadata, that can significantly enhance the system's adaptability to future requirements, making the codebase more resilient to changes and enabling an easier integration of new features or technologies.
- In the absence of clear guidelines, developers may use practices misaligned with long-term project goals. Adopting quick-fix solutions that address immediate issues can lead to a maintenance-intensive and rigid codebase.
- Without a clear comprehension of why certain practices are encouraged or discouraged, developers may inadvertently contravene these guidelines, reintroducing the issues they were meant to avoid.
- The premature addition of abstractions and too much flexibility can add unnecessary complexity in the code, harming code maintenance.

Therefore:

**Define a guideline of programming practices that should be followed or avoided by the development team to not limit the options to an architectural decision being postponed, explain to them the reason, and implement its adoptions.**

When facing uncertainties related to the software architecture, the team usually identifies possible solutions that could be adopted in the future. Each of these future options can be analyzed to see if a given programming practice can support the decision to postpone. Likewise, it can also be practices that would make it difficult to follow one of the alternatives further. Based on that, the team should communicate and elaborate a guideline to reduce the impact of that uncertainty.

The initial step in implementing the guidelines involves a thorough examination of the current state of the project to identify if any of the newly established practices are already being violated. This process is crucial as it sets the baseline from which improvements can be made. If violations are detected, planning a refactoring may become necessary.

Regular verification methods, like using Continuous Inspection, may be established to ensure the guidelines are consistently followed. This could involve automated checks integrated into the development process or scheduled code reviews. Automated checks offer efficiency and consistency, continuously scanning the codebase for deviations and ensuring compliance with the set guidelines. However, an automated verification might not be available in the toolset used by the team for some of the guidelines. On the other hand, code reviews provide a more human-centric approach, allowing for a deeper dive into the code's logic and structure. They facilitate a collaborative environment where team members can discuss and understand the application of guidelines in different contexts. This combination of automation and human oversight may help to create a robust framework for maintaining guideline adherence, serving as an auxiliary tool to ensure that the project's development remains on track and aligned with the desired architectural outcomes.

Despite all the efforts to implement the guidelines, their success heavily relies on the development team's understanding and acceptance. If team members are unclear about the purpose or reasoning behind a particular guideline, they might inadvertently find alternative methods that bypass the guideline but lead to similar problems. To prevent this, it's vital to ensure clear communication and awareness regarding the guidelines. When the developers understand the rationale behind each guideline, they are more likely to see its value and apply it correctly.

It is important to consider that this pattern is not about defining and establishing general good coding practices for several projects and for the whole code, like dependency injection, SOLID principles, or object-oriented design patterns. Instead, the programming guideline is implemented to handle a specific uncertainty, which is usually restricted to the affected features or parts of the systems.

## Consequences

The following are the consequences of using this pattern:

- The guideline reduces the potential negative impact of uncertainties that might require changes in the code.
- The guideline empowers developers to make choices that align with long-term project goals, preventing adopting practices that might limit future architectural decisions.
- Adhering to the guidelines facilitates effective communication within the team regarding architectural choices.
- Adhering to the guideline may introduce additional overhead regarding time and resources.
- When several guidelines are adopted, they might interfere with each other, and it might be difficult to adhere to both.
- Team members may experience a learning curve when adapting to new practices.
- If the development team does not fully understand or accept the guidelines, resistance or non-adherence may occur. This can lead to deviations from recommended practices, potentially reintroducing issues the guidelines aim to prevent.

## Related Patterns

Patterns that focus on modularity and isolate parts of the software, such as **Strategy** and **Proxy**, can be used to isolate parts of the code that can change. Patterns related to the usage of metadata can also decouple parts of the software, allowing them to evolve independently.

**Continuous Inspection** can be used to implement the verification if the guideline is being followed. Other patterns for software analytics can also help a team adopt software analytics practices for this purpose. These patterns can also be supported by the **Software Analytics Canvas (SA Canvas)**.

## Examples

_For instance, envision a scenario in a healthcare project where there is a need to integrate with third-party laboratories or pharmacies. In this context, the hypothesis that "The application's main functionalities work independent of unexpected errors that happen on third-party systems" encapsulates a critical uncertainty. The lack of knowledge about third-party systems makes the type of errors that might happen hard to predict. To reduce the impact of this uncertainty, a Protective Guideline was implemented to make all these interactions asynchronous. Before its implementation, this guideline was discussed and agreed with the development team. In this case, since this part will be executed in a different process, it will not interfere with the flow of the main functionality if an error happens._
