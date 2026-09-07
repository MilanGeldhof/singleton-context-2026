# -------------------------------------------------------------------------
# Data Analysis Context-Dependency
# Author: Milan Geldhof
# Date: 06/2026
# -------------------------------------------------------------------------

# Load Libraries
library(ggplot2)
library(dplyr)
library(tidyr) 
library(lme4)
library(lmerTest)
library(emmeans)
library(car)
library(effectsize)
library(MuMIn)

#-----------------------------------------------------
# 1. Initialize
#-----------------------------------------------------
# set global coding
options(contrasts = c("contr.sum", "contr.poly"))

#set this high to get t instead of z test, to estimate DF
emm_options(pbkrtest.limit = 60000, lmerTest.limit = 60000)

# Helper: Effect Size Calculation
# Computes effect size (Cohen's d equivalent) for emmeans contrasts
# sigma and DF based on https://github.com/rvlenth/emmeans/issues/398

get_eff_size <- function(contrast_obj, model, data_subset) {
  
  vc_df <- as.data.frame(VarCorr(model))
  # 2. Select rows where var2 is NA, so SD instead of COR
  sd_only <- vc_df[is.na(vc_df$var2), ]$sdcor
  sd_only <- sd_only[c(1, length(sd_only))] # take error and intercept SD
  # compute sigma
  s <- sqrt(sum(sd_only^2))
  
  all_emm_pairs <- as.data.frame(contrast_obj)
  min_df <- min(all_emm_pairs$df)
  
  results <- eff_size(contrast_obj, sigma = s, edf = min_df, method = 'identity')
  print(results)
  return(results)
}

# Define Model Wrapper to reduce repetition
run_analysis <- function(formula, data_sub) {
  model <- lmer(formula, data = data_sub, control = lmerControl(optimizer = "bobyqa",optCtrl = list(maxfun = 2e5)))
  print(summary(model))
  print(anova(model, type = 3))
  
  emm <- emmeans(model, ~ Condition, type = "response")
  return(list(model = model, emm = emm))
}

# Helper function: Formats p-values to 3 decimals, removes leading zero, and bins < .001
fmt_p_val <- function(p) {
  case_when(
    p < .001 ~ "< .001",
    TRUE     ~ paste0("= ", sub("^0\\.", ".", sprintf("%.3f", p)))
  )
}

data_path <- "C:/Users/milan/OneDrive - UGent/SingletonContext_2026/CombinedData_n141.csv"

# log in model so emmeans sees this and can back-transform
formulaTrain     <-  'log(RT) ~ Condition + TargetLoc + TrialsWithinBlock + (1 + Condition | Participant)'
formulaTest      <-  'log(RT) ~ Condition + TargetLoc + SwitchBackground + TrialsWithinBlock + (1 + Condition | Participant)'
formulaTest_null <-  'log(RT) ~ Condition_null + TargetLoc + SwitchBackground + TrialsWithinBlock + (1 + Condition | Participant)'
formulaTest_aw   <-  'log(RT) ~ Condition * AwarenessScore + TargetLoc + SwitchBackground + TrialsWithinBlock + (1 + Condition | Participant)'

#-----------------------------------------------------
# 2. Load and Preprocess Data
#-----------------------------------------------------
data <- read.csv(data_path)

# before i remove trials, mean center for model fit
data$TrialsWithinBlock <- scale(data$TrialsWithinBlock, center=TRUE, scale = FALSE)


## 2. Exclusion Criteria --------------------------------------------------
# Subject Level
all_subjID <- unique(data$Participant)

data_subj_rem <- data %>% 
  filter(Accuracy > 0.80) %>%
  filter(HasNormColorVision == 1)

removed_subj <- setdiff(all_subjID, unique(data_subj_rem$Participant))

# Trial Level (Correct responses, RT > 200ms, local 3SD filter)
data_cleaned_step1 <- data_subj_rem %>%
  filter(CorrectnessResp == 1)

data_cleaned <- data_cleaned_step1 %>%
  filter(RT >= 200) %>%
  group_by(Participant, Block) %>%
  mutate(upper_limit = mean(RT) + (3 * sd(RT))) %>%
  filter(RT <= upper_limit) %>%
  ungroup() %>%
  select(-upper_limit)


df_first <- data_cleaned %>%
  group_by(Participant) %>%
  slice(1) %>%
  ungroup()

df_vision <- data_cleaned %>%
  group_by(Participant) %>%
  filter(HasNormVision == 0) %>%
  slice(1) %>%
  ungroup()

# Summary Report
cat("\n--- EXCLUSION REPORT ---\n")
cat("Subjects removed (Acc < 80%) or vision:", length(removed_subj), "\n")
cat(sprintf("Trial removal rate correctness filter: %.2f%%\n", (1 - (nrow(data_cleaned_step1)/nrow(data_subj_rem)))*100))
cat(sprintf("Trial removal rate RT filter: %.2f%%\n", (1 - (nrow(data_cleaned)/nrow(data_cleaned_step1)))*100))
cat("M and SD accuracy of sample kept (bad vision):", round(mean(df_vision$Accuracy), 3),  round(sd(df_vision$Accuracy), 3), "\n")
cat("M and SD accuracy of sample kept:", round(mean(df_first$Accuracy), 3),  round(sd(df_first$Accuracy), 3), "\n")
cat("------------------------\n")

#write this data out, as this will be used for plotting in other scripts
write.csv(data_cleaned, gsub("CombinedData_n141", "CleanedData", data_path), row.names = FALSE)

#-----------------------------------------------------
## 3. Statistical Models 
#-----------------------------------------------------
# condition levels are = "HF_ThisContext"  "LF" "NoDist" "HF_OtherContext" "Mismatch"   "Match"   

dataA <- data_cleaned %>% 
  filter(Block == 0, Condition %in% c("HF_ThisContext", "HF_OtherContext", "LF", "NoDist")) %>% 
  mutate(Condition = dplyr::recode(Condition, "HF_OtherContext" = "LF")) %>% # there is not HF_OtherContext yet
  select(RT, Condition, Participant, TrialsWithinBlock, TargetLoc, SwitchBackground) %>%
  mutate(
    Condition = as.factor(Condition),
    Participant = as.factor(Participant),
    TargetLoc = as.factor(TargetLoc),
    SwitchBackground = as.factor(SwitchBackground),
  )

dataB <- data_cleaned %>% 
  filter(Block == 1, Condition %in% c("HF_ThisContext", "HF_OtherContext", "LF", "NoDist")) %>% 
  select(RT, Condition, Participant, TrialsWithinBlock, TargetLoc, SwitchBackground) %>%
  mutate(
    Condition = as.factor(Condition),
    Participant = as.factor(Participant),
    TargetLoc = as.factor(TargetLoc),
    SwitchBackground = as.factor(SwitchBackground),
  )


dataAB <- data_cleaned %>% 
  filter(Block == 2, Condition %in% c("Match", "Mismatch", "LF", "NoDist"))%>% 
  select(RT, Condition, Participant, TrialsWithinBlock, TargetLoc, SwitchBackground, AwarenessScore) %>%
  mutate(
    Condition = as.factor(Condition),
    Participant = as.factor(Participant),
    TargetLoc = as.factor(TargetLoc),
    SwitchBackground = as.factor(SwitchBackground),
  )


contrasts(dataAB$TargetLoc)
contrasts(dataAB$Condition)
contrasts(dataB$Condition)
contrasts(dataA$Condition)


# Fit all models here
resA <- run_analysis(formulaTrain, dataA)
resB <- run_analysis(formulaTrain, dataB)
resAB <- run_analysis(formulaTest, dataAB)
resAB_awareness <- run_analysis(formulaTest_aw, dataAB)


r.squaredGLMM(resA$model)
r.squaredGLMM(resB$model)
r.squaredGLMM(resAB$model)
r.squaredGLMM(resAB_awareness$model)


summary(resA$model)$optinfo$conv$lme4
summary(resB$model)$optinfo$conv$lme4
summary(resAB$model)$optinfo$conv$lme4
summary(resAB_awareness$model)$optinfo$conv$lme4
isSingular(resA$model)
isSingular(resB$model)
isSingular(resAB$model)
isSingular(resAB_awareness$model)
summary(resA$model)$optinfo$message
summary(resB$model)$optinfo$message
summary(resAB$model)$optinfo$message
summary(resAB_awareness$model)$optinfo$message

#-----------------------------------------------------
# Block 1 
#-----------------------------------------------------
# use 0.5 to average, and get correct emm estimates of RT
contrastA <- list(
  "Dist min NoDist" = c(HF_ThisContext = 0.5, LF = 0.5, NoDist = -1),
  "LF min HF"       = c(HF_ThisContext = -1,  LF = 1,  NoDist = 0)
)

c1 <- contrast(resA$emm, contrastA, adjust = 'holm')
print(c1)

# get effect size
ef_c1 <- as.data.frame(get_eff_size(c1, resA$model, dataA))

# combine these, and add others tests to this
stats_blockA <- cbind(as.data.frame(c1), ef_c1)
stats_blockA$Block <- "1"

#-----------------------------------------------------
# Block 2
#-----------------------------------------------------

contrastB <- list(
  "Dist min NoDist" = c(HF_OtherContext = 1/3, HF_ThisContext = 1/3, LF = 1/3, NoDist = -1),
  "LF min HF"       = c(HF_OtherContext = 0, HF_ThisContext = -1, LF = 1, NoDist = 0),
  "LF min HFofA"    = c(HF_OtherContext = -1, HF_ThisContext = 0, LF = 1, NoDist = 0)
)

c2 <- contrast(resB$emm, contrastB, adjust = 'holm')
resB$emm
print(c2)

ef_c2 <- as.data.frame(get_eff_size(c2, resB$model, dataB))

stats_blockB <- cbind(as.data.frame(c2), ef_c2)
stats_blockB$Block <- "2"
#-----------------------------------------------------
# Block 3
#-----------------------------------------------------
contrastAB <- list(
  "Dist min NoDist" =    c(LF = 1/3, Match = 1/3, Mismatch = 1/3, NoDist = -1),
  "Match min Mismatch" = c(LF = 0, Match = -1, Mismatch = 1, NoDist = 0),
  "LF min Match"    =    c(LF = 1, Match = -1, Mismatch = 0, NoDist = 0),
  "LF min Mismatch" =    c(LF = 1, Match =  0, Mismatch = -1, NoDist = 0)
)

c3 <- contrast(resAB$emm, contrastAB, adjust = 'holm')
print(resAB$emm)
print(c3)

ef_c3 <- as.data.frame(get_eff_size(c3, resAB$model, dataAB))

stats_blockAB <- cbind(as.data.frame(c3), ef_c3)
stats_blockAB$Block <- "3"


stats_df <- rbind(stats_blockA, stats_blockB, stats_blockAB)
stats_df <- stats_df[, !duplicated(names(stats_df))]

## BIC Bayes Factor
# make null model condition factor by joining 2 levels in the factor (match and mismatch) HO: they are equal so do not need different beta
dataAB$Condition_null <- dataAB$Condition
levels(dataAB$Condition_null)[levels(dataAB$Condition_null) %in% c("Match", "Mismatch")] <- "MatchMerged"

null_model <- lmer(formulaTest_null,data=dataAB, REML=F, control=lmerControl(optimizer = "bobyqa",optCtrl = list(maxfun = 2e5)))
full_model <- lmer(formulaTest,     data=dataAB, REML=F, control=lmerControl(optimizer = "bobyqa",optCtrl = list(maxfun = 2e5)))
BF10 = exp((BIC(null_model) - BIC(full_model))/2)
BF01 = exp((BIC(full_model) - BIC(null_model))/2)

round(BF01, 2)

#save stats outs, and already format for paper 

# 3. Generate the APA-formatted string column
stats_df <- stats_df %>%
  mutate(
    apa_result = paste0(
      "t(", sprintf("%.2f", df), ") = ", sprintf("%.2f", t.ratio), 
      ", p ", fmt_p_val(p.value) , 
      ", d = ", sprintf("%.2f", estimate),   
      ", 95% CI [",  sprintf("%.2f", lower.CL), ", ",  sprintf("%.2f",upper.CL), "]"
    )
  )

stats_df[] <- lapply(stats_df, function(x) {
  if (is.numeric(x)) round(x, 5) else x
})

write.csv(stats_df, gsub("CombinedData_n141.csv", "Stats_overview.csv", data_path), row.names = FALSE)

#-----------------------------------------------------
# Awareness Analysis
#-----------------------------------------------------

chance_level_awareness_score <- 1.5
sum(df_first$SelfReportedAwareness == 1) / sum(df_first$SelfReportedAwareness != 3)

# 1) all subs vs chance level
t_res <-    t.test(df_first$AwarenessScore, mu = chance_level_awareness_score)
d_res <-  cohens_d(df_first$AwarenessScore, mu = chance_level_awareness_score)

sprintf("(mean = %.2f, SD = %.2f)", mean(df_first$AwarenessScore, na.rm = TRUE), sd(df_first$AwarenessScore, na.rm = TRUE))
sprintf("t(%.0f) = %.2f, p %s, d = %.2f, 95%% CI [%.2f, %.2f]", t_res$parameter, t_res$statistic, fmt_p_val(t_res$p.value), d_res$Cohens_d,d_res$CI_low, d_res$CI_high)

# 2) 'aware' vs 'unaware' self report
t_res <-  t.test(AwarenessScore ~ SelfReportedAwareness, data = df_first, paired=FALSE)
d_res <-  cohens_d(AwarenessScore ~ SelfReportedAwareness, data = df_first)

aggregate(AwarenessScore ~ SelfReportedAwareness, data = df_first, FUN = mean)
aggregate(AwarenessScore ~ SelfReportedAwareness, data = df_first, FUN = sd)

sprintf("t(%.0f) = %.2f, p %s, d = %.2f, 95%% CI [%.2f, %.2f]", t_res$parameter, t_res$statistic, fmt_p_val(t_res$p.value), d_res$Cohens_d,d_res$CI_low, d_res$CI_high)


# 3) interaction with conditions?
anova(resAB_awareness$model, type=3)


