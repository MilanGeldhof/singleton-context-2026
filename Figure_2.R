library(dplyr)
library(ggplot2)
library(ggforce)
library(ggh4x)
library(dplyr)
library(tidyr)
library(stringr)
library(ggpubr)

# ==========================================
# CONFIGURATION SECTION
# ==========================================
block_label_size <- 12
xy_size <- 11
tick_size <- 9
pval_size <- 5

# ==========================================
# LOAD DATA
# ==========================================
data_path <- "C:/Users/milan/OneDrive - UGent/SingletonContext_2026/CleanedData.csv"
stats_path <- "C:/Users/milan/OneDrive - UGent/SingletonContext_2026/Stats_overview.csv"

data <- read.csv(data_path)

data <- data %>%
  mutate(
    Condition = case_when(
      
      Block == 0 & Condition == "HF_OtherContext" ~ "Low-Freq",
      Block == 0 & Condition == "HF_ThisContext" ~ "High-Freq Match",
      
      Block == 1 & Condition == "HF_OtherContext" ~ "High-Freq Mismatch",
      Block == 1 & Condition == "HF_ThisContext" ~ "High-Freq Match",
      
      Condition == "LF" ~ "Low-Freq",
      Condition == "NoDist" ~ "No Distractor",
      Condition == "Match" ~ "High-Freq Match",
      Condition == "Mismatch" ~ "High-Freq Mismatch",
      
      TRUE ~ NA_character_
    )
  )


sig_df <-  read.csv(stats_path) %>%
  filter(!str_detect(contrast, "NoDist")) %>%
  separate(
    contrast,
    into = c("group1", "group2"),
    sep = " min "
  ) %>%
  mutate(
  pvalue = case_when(
    p.value < .001 ~ "***",
    p.value < .01  ~ "**",
    p.value < .05  ~ "*",
    TRUE ~ "ns")) %>%
  
  mutate(
    group1 = recode(
      group1,
      "LF" = "Low-Freq",
      "HF" = "High-Freq Match", 
      "HFofA" = "High-Freq Mismatch",
      "Mismatch" = "High-Freq Mismatch", 
      "Match" = "High-Freq Match", 
    ),
    group2 = recode(
      group2,
      "LF" = "Low-Freq",
      "HF" = "High-Freq Match", 
      "HFofA" = "High-Freq Mismatch",
      "Mismatch" = "High-Freq Mismatch", 
      "Match" = "High-Freq Match", 
    )
  )
      
sig_df$ypos <- c(1440, 1200, 1200, 1080 ,1080, 1080)
sig_df$Block <- factor(
  sig_df$Block,
  levels = c(1, 2, 3),
  labels = c("Learning Block 1", "Learning Block 2", "Testing Block")
)


# ==========================================
# SUMMARY: mean RT + 95% CI
# ==========================================

summary_RT <- data %>%
  group_by(Block, Condition) %>%
  summarise(
    mean_RT = mean(RT, na.rm = TRUE),
    sd_RT   = sd(RT, na.rm = TRUE),
    n       = n(),
    sem_RT  = sd_RT / sqrt(n),
    ci95    = 1.96 * sem_RT,
    .groups = "drop"
  )


# ==========================================
# FACTOR ORDERING
# ==========================================
summary_RT$Condition <- factor(
  summary_RT$Condition,
  levels = c("No Distractor", "High-Freq Match", "High-Freq Mismatch", "Low-Freq")
)

summary_RT$Block <- factor(
  summary_RT$Block,
  levels = c(0, 1, 2),
  labels = c("Learning Block 1", "Learning Block 2", "Testing Block")
)

# ==========================================
# PLOT
# ==========================================
ggplot(summary_RT, aes(x = Condition, y = mean_RT, fill = Condition)) +
  
  geom_bar(
    stat = "identity",
    width = 0.8,
    linewidth = 0.3,
    color = "black") +
  
  geom_errorbar(
    aes(
      ymin = mean_RT - ci95,
      ymax = mean_RT + ci95
    ),
    width = 0.2,
    linewidth = 0.3,
    color = "black"
  ) +
  
  facet_wrap(~ Block, nrow = 1) +
  
  scale_fill_manual(values = c(
    "No Distractor" = "#2F2F2F",
    "High-Freq Match" = "#215F9A",
    "High-Freq Mismatch" = "#71C5BD",
    "Low-Freq" = "#7F7F7F"
  )) +
  
  labs(
    x = "Condition",
    y = "Reaction Time (ms)"
  ) +
  
  coord_cartesian(ylim = c(880, 1450)) +
  scale_y_continuous(breaks = seq(880, 1450, by=40)) +
  
  
  theme_classic(base_family = "sans") +
  theme(
    panel.grid.major = element_line(),
    panel.grid.minor = element_line(),
    
    aspect.ratio = 1,
    legend.position = "none",                    # Remove legend
    axis.title = element_text(size = xy_size, face = "bold"),  # Larger axis titles
    axis.text = element_text(size = tick_size),         # Larger tick labels
    axis.text.x = element_text(
      angle = 20,                                # Rotate x labels
      hjust = 1,
      vjust = 1
    ),
    strip.text = element_text(size = block_label_size, face = "bold")   # Larger facet labels
  
  ) + 
  stat_pvalue_manual(
    sig_df,
    xmin = "group1",
    xmax = "group2",
    facet = "Block",
    y.position = "ypos",
    step.increase = 0.1,
    size=pval_size,
    bracket.size=0.4,
    tip.length=0.01,
    step.group.by = "Block",
    label = "pvalue",
    inherit.aes = FALSE
  )


ggsave(
  filename = "Figure_2.svg",
  width = 18,
  height = 10,
  units = "cm"
)

ggsave(
  filename = "Figure_2.eps",
  width = 18,
  height = 10,
  units = "cm",
  device = cairo_ps
)


