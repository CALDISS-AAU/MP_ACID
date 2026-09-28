library(ggplot2)
library(dplyr)
library(readr)

data_p = file.path(".", "Output", "Screengetter", "event_frames_tagged.csv")

event_frames <- read_csv(
  data_p,
)

# Exclude observations without a trajectory label and count each feeling event
# once. The CSV contains one row for every frame belonging to an event.
plot_data <- event_frames |>
  filter(!is.na(tag_trajectory)) |>
  distinct(group, task, feeling_timestamp, tag_trajectory)

tag_trajectory_data <- plot_data |>
  count(tag_trajectory, name = "count") |>
  mutate(percent = count / sum(count))

tag_trajectory_by_task_data <- plot_data |>
  count(task, tag_trajectory, name = "count") |>
  group_by(task) |>
  mutate(prop = count / sum(count)) |>
  ungroup()

# Plots
tag_trajectory_plot <- ggplot(
  tag_trajectory_data,
  aes(x = tag_trajectory, y = percent)
  ) +
  geom_col(fill = "steelblue") +
  coord_flip() +
  scale_y_continuous(labels = scales::label_percent()) +
  labs(
    title = "UI trajectory",
    x = NULL,
    y = "Percent"
  ) +
  theme_minimal()
  
tag_trajectory_by_task_plot <- ggplot(
  tag_trajectory_by_task_data,
  aes(x = tag_trajectory, y = prop, fill = as.factor(task))) +
  geom_col() +
  coord_flip() +
  scale_y_continuous(labels = scales::label_percent()) +
  labs(
    title = "UI trajectory by task",
    x = NULL,
    y = "Percent",
    fill = "Task"
  ) +
  theme_minimal()

# Store plots
ggsave(
  "tag_trajectory_percent.png",
  tag_trajectory_plot,
  width = 10,
  height = 7,
  dpi = 300
)
ggsave(
  "tag_trajectory_by_task_percent.png",
  tag_trajectory_by_task_plot,
  width = 10,
  height = 7,
  dpi = 300
)